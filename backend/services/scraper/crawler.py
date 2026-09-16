"""
Unified academic resource crawler for MarkMint.
Coordinates:
- Studique API discovery & unit-wise resources.
- The Helpers Semesters 1-8 discovery & recursive Google Drive folder traversal.
- Resilient streaming downloads, strict PDF verification, deduplication.
- Deterministic classification & canonical curriculum resolution.
- Live progress reporting, atomic manifest checkpointing, and graceful resume.
"""

import os
import re
import time
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import quote, urlparse
import requests

from sqlalchemy.orm import Session

from .models import (
    ManifestRecord,
    DownloadStatus,
    ResourceClassification,
    CurriculumMatchState,
    AuditReport,
    ActionRequiredItem,
)
from .classifier import ResourceClassifier
from .curriculum_resolver import CurriculumResolver
from .drive_handler import GoogleDriveHandler, GoogleDriveItem
from .downloader import ResourceDownloader, sanitize_filesystem_name
from .manifest import ManifestManager
from .ingester import CorpusIngester

logger = logging.getLogger(__name__)


class AcademicResourceCrawler:
    """Orchestrates multi-source academic discovery, verification, and ingestion."""

    STUDIQUE_API_URL = "https://studique.in/api/resource/list"
    HELPERS_CHUNK_URL = "https://thehelpers.tech/_next/static/chunks/325-65fb825d127b8f94.js"
    HELPERS_BASE_URL = "https://thehelpers.tech"

    def __init__(
        self,
        db: Session,
        manifest_manager: Optional[ManifestManager] = None,
        downloader: Optional[ResourceDownloader] = None,
        rate_limit_seconds: float = 0.5,
        download_only: bool = False,
        headless: bool = True,
    ):
        self.db = db
        self.manifest = manifest_manager or ManifestManager()
        self.downloader = downloader or ResourceDownloader()
        self.ingester = CorpusIngester(db)
        self.resolver = CurriculumResolver(db)
        self.rate_limit_seconds = rate_limit_seconds
        self.download_only = download_only
        self.headless = headless

        self._last_request_time = 0.0

    def _sleep_rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
        self._last_request_time = time.time()

    # =========================================================================
    # STUDIQUE DISCOVERY
    # =========================================================================

    def discover_studique(
        self,
        semester_filter: Optional[int] = None,
        subject_filter: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> List[ManifestRecord]:
        """
        Discovers unit-wise resources, PYQs, and syllabi from Studique API.
        """
        logger.info("Connecting to Studique resource endpoint: %s", self.STUDIQUE_API_URL)
        headers = {"User-Agent": self.downloader.USER_AGENT}
        try:
            r = requests.get(self.STUDIQUE_API_URL, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.error("Failed to fetch Studique catalog: %s", e)
            return []

        subjects = data.get("subjects", [])
        logger.info("Discovered %d subjects from Studique catalog.", len(subjects))

        discovered_records: List[ManifestRecord] = []

        for subj_data in subjects:
            subj_name = subj_data.get("name", "").strip()
            subj_sem = str(subj_data.get("year", subj_data.get("semester", ""))).strip()

            if semester_filter and subj_sem and str(semester_filter) != subj_sem:
                continue

            if subject_filter and subject_filter.lower() not in subj_name.lower():
                continue

            # Process PPTs (Lecture Notes / Study Material)
            for ppt in subj_data.get("ppts", []):
                if max_items and len(discovered_records) >= max_items:
                    break
                name = ppt.get("name", "Lecture Notes")
                fkey = ppt.get("fileKey")
                if not fkey:
                    continue

                source_url = f"https://www.studique.in/unitwise#{quote(subj_name)}"
                direct_url = f"https://drive.google.com/uc?export=download&id={fkey}"

                unit_match = re.search(r"unit\s*(\d+)", name, re.IGNORECASE)
                unit_str = f"Unit {unit_match.group(1)}" if unit_match else None

                rec = ManifestRecord(
                    source_site="Studique",
                    source_url=source_url,
                    resolved_url=direct_url,
                    semester=subj_sem or "1",
                    subject=subj_name,
                    unit=unit_str,
                    title=f"{subj_name} - {name}",
                    resource_type="ppt",
                    google_drive_id=fkey,
                    download_status=DownloadStatus.DISCOVERED,
                )
                discovered_records.append(rec)

            # Process PYQs
            for pyq in subj_data.get("pyqs", []):
                if max_items and len(discovered_records) >= max_items:
                    break
                name = pyq.get("name", "PYQ")
                fkey = pyq.get("fileKey")
                if not fkey:
                    continue

                source_url = f"https://www.studique.in/unitwise#{quote(subj_name)}"
                direct_url = f"https://drive.google.com/uc?export=download&id={fkey}"

                rec = ManifestRecord(
                    source_site="Studique",
                    source_url=source_url,
                    resolved_url=direct_url,
                    semester=subj_sem or "1",
                    subject=subj_name,
                    title=f"{subj_name} - PYQ {name}",
                    resource_type="pyq",
                    google_drive_id=fkey,
                    download_status=DownloadStatus.DISCOVERED,
                )
                discovered_records.append(rec)

            # Process Syllabi
            for syl in subj_data.get("syllabus", []):
                if max_items and len(discovered_records) >= max_items:
                    break
                name = syl.get("name", "Syllabus")
                fkey = syl.get("fileKey")
                if not fkey:
                    continue

                source_url = f"https://www.studique.in/unitwise#{quote(subj_name)}"
                direct_url = f"https://drive.google.com/uc?export=download&id={fkey}"

                rec = ManifestRecord(
                    source_site="Studique",
                    source_url=source_url,
                    resolved_url=direct_url,
                    semester=subj_sem or "1",
                    subject=subj_name,
                    title=f"{subj_name} - {name}",
                    resource_type="syllabus",
                    google_drive_id=fkey,
                    download_status=DownloadStatus.DISCOVERED,
                )
                discovered_records.append(rec)

            if max_items and len(discovered_records) >= max_items:
                break

        logger.info("Generated %d candidate resource records from Studique.", len(discovered_records))
        return discovered_records

    # =========================================================================
    # THE HELPERS DISCOVERY
    # =========================================================================

    def discover_thehelpers(
        self,
        semester_filter: Optional[int] = None,
        subject_filter: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> List[ManifestRecord]:
        """
        Discovers resources from The Helpers across Semesters 1 through 8.
        Parses webpack asset catalog chunk (or dynamic pages) and recursively traverses Drive folders.
        """
        logger.info("Fetching The Helpers asset catalog: %s", self.HELPERS_CHUNK_URL)
        headers = {"User-Agent": self.downloader.USER_AGENT}
        try:
            r = requests.get(self.HELPERS_CHUNK_URL, headers=headers, timeout=15)
            r.raise_for_status()
            text = r.text
        except Exception as e:
            logger.error("Failed to fetch The Helpers asset chunk: %s", e)
            return []

        # Extract semester-to-subjects mapping: r={1:[...], 2:[...], ... 8:[...]}
        sem_match = re.search(r'([a-zA-Z0-9_$]+)\s*=\s*(\{1:\[.*?8:\[.*?\}\])', text)
        semester_map: Dict[int, List[str]] = {}
        if sem_match:
            try:
                # Convert JS object to JSON
                raw_obj = sem_match.group(2)
                # Replace key numbers with quotes
                raw_json = re.sub(r'(\d+):', r'"\1":', raw_obj)
                sem_dict = json.loads(raw_json)
                for k, v in sem_dict.items():
                    semester_map[int(k)] = v
            except Exception as e:
                logger.warning("Failed to parse JSON semester map directly: %s. Using regex extraction.", e)

        if not semester_map:
            # Fallback regex extraction of semester arrays
            for sem in range(1, 9):
                match = re.search(rf'{sem}:\[([^\]]+)\]', text)
                if match:
                    raw_items = re.findall(r'"([^"]+)"', match.group(1))
                    semester_map[sem] = raw_items

        logger.info(
            "Extracted semester catalog for %d semesters from The Helpers.",
            len(semester_map)
        )

        # Extract resources mapping: l={"Calculus And Linear Algebra":{pyqs:[...],notes:[...]}}
        # Search for subject resource objects
        resource_blocks = re.findall(r'"([^"]+)":\{([^{}]+(?:\{[^{}]*\}[^{}]*)*)\}', text)
        subject_resources: Dict[str, List[Dict[str, str]]] = {}

        for subj_name, block in resource_blocks:
            # Look for pyqs, notes, etc.
            items = re.findall(r'name:"([^"]+)",url:"([^"]+)"', block)
            if items:
                res_list = [{"name": n, "url": u} for n, u in items]
                subject_resources[subj_name] = res_list

        discovered_records: List[ManifestRecord] = []

        for sem, subjects in semester_map.items():
            if semester_filter and semester_filter != sem:
                continue

            for subj in subjects:
                if subject_filter and subject_filter.lower() not in subj.lower():
                    continue

                resources = subject_resources.get(subj, [])
                source_subject_url = f"{self.HELPERS_BASE_URL}/semesters/{sem}/subjects/{quote(subj)}"

                for res in resources:
                    if max_items and len(discovered_records) >= max_items:
                        break

                    res_name = res["name"]
                    raw_url = res["url"]

                    # Check if Google Drive Folder
                    if GoogleDriveHandler.is_drive_folder(raw_url):
                        logger.info("Found Google Drive folder for '%s' -> %s. Traversing...", subj, raw_url)
                        self._sleep_rate_limit()
                        folder_items, action_req = GoogleDriveHandler.traverse_folder(
                            raw_url,
                            current_folder_path=f"{subj}/{res_name}",
                            max_depth=5,
                        )

                        if action_req:
                            rec = ManifestRecord(
                                source_site="TheHelpers",
                                source_url=source_subject_url,
                                resolved_url=raw_url,
                                semester=str(sem),
                                subject=subj,
                                title=f"{subj} - {res_name} (Folder)",
                                resource_type="folder",
                                google_drive_id=GoogleDriveHandler.extract_folder_id(raw_url),
                                download_status=DownloadStatus.FAILED,
                                failure_reason=action_req.problem,
                                action_required=action_req,
                            )
                            discovered_records.append(rec)
                            continue

                        # Add each child item discovered inside folder
                        logger.info("Traversed folder '%s': discovered %d child files.", res_name, len(folder_items))
                        for child in folder_items:
                            if max_items and len(discovered_records) >= max_items:
                                break
                            child_rec = ManifestRecord(
                                source_site="TheHelpers",
                                source_url=source_subject_url,
                                resolved_url=child.direct_url,
                                semester=str(sem),
                                subject=subj,
                                title=f"{subj} - {child.name}",
                                resource_type="file",
                                google_drive_id=child.item_id,
                                drive_folder_path=child.folder_path,
                                download_status=DownloadStatus.DISCOVERED,
                            )
                            discovered_records.append(child_rec)

                    else:
                        # Individual file
                        direct_url = GoogleDriveHandler.get_direct_download_url(raw_url)
                        drive_id = GoogleDriveHandler.extract_file_id(raw_url)

                        rec = ManifestRecord(
                            source_site="TheHelpers",
                            source_url=source_subject_url,
                            resolved_url=direct_url,
                            semester=str(sem),
                            subject=subj,
                            title=f"{subj} - {res_name}",
                            resource_type="file",
                            google_drive_id=drive_id,
                            download_status=DownloadStatus.DISCOVERED,
                        )
                        discovered_records.append(rec)

                if max_items and len(discovered_records) >= max_items:
                    break

        logger.info("Generated %d candidate resource records from The Helpers.", len(discovered_records))
        return discovered_records

    # =========================================================================
    # PROCESS & EXECUTE PIPELINE
    # =========================================================================

    def process_record(self, record: ManifestRecord, resume: bool = True) -> ManifestRecord:
        """
        Executes full pipeline on a single manifest record:
        Download -> Validation -> Classification -> Curriculum Resolution -> Ingestion -> Manifest Save.
        """
        print(f"\n--> Processing [{record.source_site}] {record.title}")

        # 1. Check resume status
        if resume and self.manifest.is_already_completed(
            record.source_site, record.source_url, record.google_drive_id
        ):
            print(f"    [SKIP] Already completed in manifest (ID: {record.google_drive_id or record.source_url})")
            existing = self.manifest.get_by_drive_id(record.google_drive_id) if record.google_drive_id else None
            return existing or record

        # 2. Resolve URL
        download_url = record.resolved_url or record.source_url
        if not download_url:
            record.download_status = DownloadStatus.FAILED
            record.failure_reason = "No valid download URL could be resolved"
            return self.manifest.add_or_update_record(record)

        self._sleep_rate_limit()

        # 3. Stream download to temporary file
        print(f"    [DOWNLOADING] {download_url[:80]}...")
        temp_path, error = self.downloader.download_to_temp(download_url)
        if error or not temp_path:
            print(f"    [FAILED] Download error: {error}")
            record.download_status = DownloadStatus.FAILED
            record.failure_reason = error or "Download failed"
            if "authentication" in (error or "").lower() or "permission" in (error or "").lower():
                record.action_required = ActionRequiredItem(
                    source=record.source_site,
                    url=download_url,
                    problem=error or "Access denied",
                    what_is_needed="Provide public viewing permission or direct download link",
                )
            return self.manifest.add_or_update_record(record)

        # 4. Strict PDF Validation
        print("    [VALIDATING] Checking magic bytes and PDF structure...")
        val_result = self.downloader.validate_pdf_file(temp_path)
        if not val_result.is_valid:
            print(f"    [INVALID] Rejected: {val_result.failure_reason}")
            record.download_status = DownloadStatus.INVALID
            record.failure_reason = val_result.failure_reason
            record.file_size = val_result.file_size
            try:
                os.remove(temp_path)
            except OSError:
                pass
            return self.manifest.add_or_update_record(record)

        record.sha256 = val_result.sha256
        record.file_size = val_result.file_size

        # 5. SHA-256 Deduplication check
        existing_record = self.manifest.get_by_sha256(record.sha256)
        if existing_record and existing_record.local_path and os.path.exists(existing_record.local_path):
            print(f"    [DUPLICATE] Identical SHA-256 ({record.sha256[:8]}...) exists at: {existing_record.local_path}")
            record.download_status = DownloadStatus.DUPLICATE
            record.local_path = existing_record.local_path
            record.classification = existing_record.classification
            record.classification_confidence = existing_record.classification_confidence
            record.classification_reasons = existing_record.classification_reasons
            record.extracted_year = existing_record.extracted_year
            record.assessment_type = existing_record.assessment_type
            record.curriculum_status = existing_record.curriculum_status
            record.course_id = existing_record.course_id
            record.curriculum_mapping_id = existing_record.curriculum_mapping_id

            try:
                os.remove(temp_path)
            except OSError:
                pass

            # Ingest to attach provenance record
            if not self.download_only:
                self.ingester.ingest_record(record)

            return self.manifest.add_or_update_record(record)

        # 6. Classification
        classification = ResourceClassifier.classify(
            title=record.title,
            filename=record.title,
            source_type=record.resource_type,
            drive_path=record.drive_folder_path,
        )
        record.classification = classification.category
        record.classification_confidence = classification.confidence
        record.classification_reasons = classification.reasons
        record.extracted_year = classification.extracted_year
        record.assessment_type = classification.assessment_type

        print(f"    [CLASSIFIED] {record.classification.value} (conf={record.classification_confidence})")
        if record.extracted_year:
            print(f"                 Extracted Year: {record.extracted_year}")
        if record.assessment_type:
            print(f"                 Assessment Type: {record.assessment_type}")

        # 7. Canonical Curriculum Resolution
        match_result = self.resolver.resolve(
            subject_name=record.subject or "",
            semester=record.semester,
        )
        record.curriculum_status = match_result.status
        record.course_id = match_result.course_id
        record.curriculum_mapping_id = match_result.curriculum_mapping_id

        print(f"    [CURRICULUM] {record.curriculum_status.value} (Course ID: {record.course_id or 'None'}) - {match_result.notes}")

        # 8. Store verified PDF into deterministic corpus directory
        destination_path = self.downloader.build_destination_path(
            semester=record.semester,
            subject=record.subject,
            classification=record.classification.value,
            filename=sanitize_filesystem_name(record.title),
            drive_folder_path=record.drive_folder_path,
        )
        stored_path = self.downloader.store_verified_file(temp_path, destination_path)
        record.local_path = stored_path
        record.download_status = DownloadStatus.DOWNLOADED

        print(f"    [STORED] {stored_path}")

        # 9. Database Ingestion
        if not self.download_only:
            print("    [INGESTING] Feeding into MarkMint database pipeline...")
            self.ingester.ingest_record(record)
            print(f"    [INGESTED] Status: {record.ingestion_status}")

        return self.manifest.add_or_update_record(record)

    def run(
        self,
        source: str = "all",
        semester: Optional[int] = None,
        subject: Optional[str] = None,
        limit: Optional[int] = None,
        resume: bool = True,
    ) -> AuditReport:
        """
        Executes full crawl & processing across specified sources.
        """
        print("=" * 70)
        print("  MARKMINT ACADEMIC RESOURCE CRAWLER PIPELINE")
        print(f"  Source: {source} | Semester: {semester or 'All'} | Limit: {limit or 'No limit'}")
        print("=" * 70)

        candidates: List[ManifestRecord] = []
        sources_crawled = []

        # Phase 1: Discovery
        if source in ["studique", "all"]:
            sources_crawled.append("Studique")
            candidates.extend(
                self.discover_studique(
                    semester_filter=semester,
                    subject_filter=subject,
                    max_items=limit,
                )
            )

        if source in ["helpers", "all"]:
            sources_crawled.append("TheHelpers")
            candidates.extend(
                self.discover_thehelpers(
                    semester_filter=semester,
                    subject_filter=subject,
                    max_items=limit,
                )
            )

        print(f"\n[Discovery Complete] Found {len(candidates)} candidate resources across {sources_crawled}.")

        # Phase 2: Processing (Download, Validate, Classify, Map, Ingest)
        processed_count = 0
        try:
            for rec in candidates:
                if limit and processed_count >= limit:
                    print(f"\nReached batch limit of {limit} resources.")
                    break

                self.process_record(rec, resume=resume)
                processed_count += 1

        except KeyboardInterrupt:
            print("\n[!] Crawl interrupted by user. All progress saved in manifest.")

        # Phase 3: Final Audit Report
        report = self.manifest.generate_audit_report(sources_crawled=sources_crawled)
        return report
