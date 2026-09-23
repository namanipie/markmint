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

    def _sleep_rate_limit(self, domain: Optional[str] = None):
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
        from backend.models.core import CurriculumMapping
        from .curriculum_resolver import normalize_text

        # Cache authoritative catalog subject semesters
        catalog_mappings = self.db.query(CurriculumMapping.subject_name, CurriculumMapping.semester).all()
        subj_to_sems: Dict[str, Set[int]] = {}
        supported_catalog_sems: Set[int] = set()
        for c_name, c_sem in catalog_mappings:
            if isinstance(c_sem, int) and c_sem > 0:
                subj_to_sems.setdefault(normalize_text(c_name), set()).add(c_sem)
                supported_catalog_sems.add(c_sem)

        # Early rejection for invalid or unsupported semester filters
        if semester_filter is not None:
            if not isinstance(semester_filter, int) or semester_filter <= 0 or (supported_catalog_sems and semester_filter not in supported_catalog_sems):
                logger.warning("Requested semester_filter=%s is invalid or not in supported catalog semesters %s.", semester_filter, supported_catalog_sems)
                return []

        for subj_data in subjects:
            subj_name = subj_data.get("name", "").strip()
            norm_name = normalize_text(subj_name)
            alias_name = self.resolver.KNOWN_ALIASES.get(norm_name, subj_name)
            norm_alias = normalize_text(alias_name)

            # Determine valid canonical semesters for this subject
            valid_sems: Set[int] = set()
            for c_norm, sems in subj_to_sems.items():
                if norm_alias == c_norm or norm_alias in c_norm or c_norm in norm_alias:
                    valid_sems.update(sems)

            # Enforce positive integer semesters from authoritative catalog
            positive_sems = {s for s in valid_sems if isinstance(s, int) and s > 0}
            if not positive_sems:
                # Subject not recognized in authoritative curriculum catalog
                continue

            if semester_filter is not None:
                if semester_filter not in positive_sems:
                    continue
                assigned_sem = str(semester_filter)
            else:
                assigned_sem = str(min(positive_sems))

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
                    sources=["Studique"],
                    source_urls=[source_url],
                    resolved_urls=[direct_url],
                    drive_ids=[fkey],
                    google_drive_id=fkey,
                    resource_id=f"studique_{fkey}",
                    semester=assigned_sem,
                    subject=subj_name,
                    unit=unit_str,
                    title=f"{subj_name} - {name}",
                    resource_type="ppt",
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
                    sources=["Studique"],
                    source_urls=[source_url],
                    resolved_urls=[direct_url],
                    drive_ids=[fkey],
                    google_drive_id=fkey,
                    resource_id=f"studique_{fkey}",
                    semester=assigned_sem,
                    subject=subj_name,
                    title=f"{subj_name} - PYQ {name}",
                    resource_type="pyq",
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
                    sources=["Studique"],
                    source_urls=[source_url],
                    resolved_urls=[direct_url],
                    drive_ids=[fkey],
                    google_drive_id=fkey,
                    resource_id=f"studique_{fkey}",
                    semester=assigned_sem,
                    subject=subj_name,
                    title=f"{subj_name} - {name}",
                    resource_type="syllabus",
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

        from backend.models.core import CurriculumMapping
        from .curriculum_resolver import normalize_text

        # Cache authoritative catalog subject semesters
        catalog_mappings = self.db.query(CurriculumMapping.subject_name, CurriculumMapping.semester).all()
        subj_to_sems: Dict[str, Set[int]] = {}
        supported_catalog_sems: Set[int] = set()
        for c_name, c_sem in catalog_mappings:
            if isinstance(c_sem, int) and c_sem > 0:
                subj_to_sems.setdefault(normalize_text(c_name), set()).add(c_sem)
                supported_catalog_sems.add(c_sem)

        # Early rejection for invalid or unsupported semester filters
        if semester_filter is not None:
            if not isinstance(semester_filter, int) or semester_filter <= 0 or (supported_catalog_sems and semester_filter not in supported_catalog_sems):
                logger.warning("Requested semester_filter=%s is invalid or not in supported catalog semesters %s.", semester_filter, supported_catalog_sems)
                return []

        # Robust brace-matching subject resource extraction (handles both quoted and unquoted subject names)
        subject_resources: Dict[str, List[Dict[str, str]]] = {}
        for sem, subjects in semester_map.items():
            if not isinstance(sem, int) or sem <= 0:
                continue
            if supported_catalog_sems and sem not in supported_catalog_sems:
                continue
            if semester_filter is not None and semester_filter != sem:
                continue
            for subj in subjects:
                escaped_subj = re.escape(subj)
                pattern = rf'(?:"{escaped_subj}"|{escaped_subj})\s*:\s*\{{'
                m = re.search(pattern, text)
                if m:
                    start_idx = m.end() - 1  # at '{'
                    depth = 0
                    end_idx = start_idx
                    for i in range(start_idx, len(text)):
                        if text[i] == '{':
                            depth += 1
                        elif text[i] == '}':
                            depth -= 1
                            if depth == 0:
                                end_idx = i + 1
                                break
                    block = text[start_idx:end_idx]
                    items = re.findall(r'name\s*:\s*"([^"]+)"\s*,\s*url\s*:\s*"([^"]+)"', block)
                    if items:
                        subject_resources[subj] = [{"name": n, "url": u} for n, u in items]

        discovered_records: List[ManifestRecord] = []

        for sem, subjects in semester_map.items():
            if not isinstance(sem, int) or sem <= 0:
                continue
            if supported_catalog_sems and sem not in supported_catalog_sems:
                continue
            if semester_filter is not None and semester_filter != sem:
                continue

            for subj in subjects:
                if subject_filter and subject_filter.lower() not in subj.lower():
                    continue

                # Validate subject against authoritative catalog
                norm_name = normalize_text(subj)
                alias_name = self.resolver.KNOWN_ALIASES.get(norm_name, subj)
                norm_alias = normalize_text(alias_name)
                valid_sems: Set[int] = set()
                for c_norm, sems in subj_to_sems.items():
                    if norm_alias == c_norm or norm_alias in c_norm or c_norm in norm_alias:
                        valid_sems.update(sems)

                if subj_to_sems and not valid_sems:
                    # Subject not recognized in authoritative curriculum catalog
                    continue
                if valid_sems and sem not in valid_sems:
                    # Subject is not associated with this semester in authoritative catalog
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
                        folder_items, action = GoogleDriveHandler.traverse_folder(raw_url)

                        if action:
                            rec = ManifestRecord(
                                source_site="TheHelpers",
                                source_url=source_subject_url,
                                resolved_url=raw_url,
                                sources=["TheHelpers"],
                                source_urls=[source_subject_url],
                                resolved_urls=[raw_url],
                                semester=str(sem),
                                subject=subj,
                                title=f"{subj} - {res_name}",
                                resource_type="folder",
                                download_status=DownloadStatus.FAILED,
                                terminal_status="ACCESS_BLOCKED",
                                action_required=action,
                                failure_reason=action.problem,
                            )
                            discovered_records.append(rec)
                            continue

                        # Add each child item discovered inside folder
                        logger.info("Traversed folder '%s': discovered %d child files.", res_name, len(folder_items))
                        for child in folder_items:
                            if max_items and len(discovered_records) >= max_items:
                                break
                            child_drive_id = child.item_id
                            child_rec = ManifestRecord(
                                source_site="TheHelpers",
                                source_url=source_subject_url,
                                resolved_url=child.direct_url,
                                sources=["TheHelpers"],
                                source_urls=[source_subject_url],
                                resolved_urls=[child.direct_url],
                                drive_ids=[child_drive_id] if child_drive_id else [],
                                google_drive_id=child_drive_id,
                                resource_id=f"helpers_{child_drive_id}" if child_drive_id else f"helpers_{abs(hash(child.direct_url))}",
                                semester=str(sem),
                                subject=subj,
                                title=f"{subj} - {child.name}",
                                resource_type="file",
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
                            sources=["TheHelpers"],
                            source_urls=[source_subject_url],
                            resolved_urls=[direct_url],
                            drive_ids=[drive_id] if drive_id else [],
                            google_drive_id=drive_id,
                            resource_id=f"helpers_{drive_id}" if drive_id else f"helpers_{abs(hash(direct_url))}",
                            semester=str(sem),
                            subject=subj,
                            title=f"{subj} - {res_name}",
                            resource_type="file",
                            download_status=DownloadStatus.DISCOVERED,
                        )
                        discovered_records.append(rec)

                if max_items and len(discovered_records) >= max_items:
                    break

        logger.info("Generated %d candidate resource records from The Helpers.", len(discovered_records))
        return discovered_records

    @classmethod
    def build_union_graph(
        cls,
        studique_records: List[ManifestRecord],
        helpers_records: List[ManifestRecord],
    ) -> List[ManifestRecord]:
        """
        Unifies discovered records across Studique and The Helpers into a single deduplicated graph.
        Merges records that share the same Google Drive file ID or matching direct download URLs,
        preserving multi-source provenance.
        """
        drive_id_map: Dict[str, ManifestRecord] = {}
        url_map: Dict[str, ManifestRecord] = {}
        merged_records: List[ManifestRecord] = []

        all_candidates = studique_records + helpers_records
        logger.info(
            "Building Union Graph from %d candidate records (%d Studique, %d The Helpers)...",
            len(all_candidates), len(studique_records), len(helpers_records)
        )

        for rec in all_candidates:
            primary_drive_id = rec.google_drive_id or (rec.drive_ids[0] if rec.drive_ids else None)
            matched_existing: Optional[ManifestRecord] = None

            if primary_drive_id and primary_drive_id in drive_id_map:
                matched_existing = drive_id_map[primary_drive_id]
            elif rec.resolved_url and rec.resolved_url in url_map:
                matched_existing = url_map[rec.resolved_url]

            if matched_existing:
                # Merge multi-source provenance
                for s in rec.sources or [rec.source_site]:
                    if s and s not in matched_existing.sources:
                        matched_existing.sources.append(s)
                matched_existing.source_site = ", ".join(sorted(matched_existing.sources))

                for su in rec.source_urls or [rec.source_url]:
                    if su and su not in matched_existing.source_urls:
                        matched_existing.source_urls.append(su)

                for ru in rec.resolved_urls or [rec.resolved_url]:
                    if ru and ru not in matched_existing.resolved_urls:
                        matched_existing.resolved_urls.append(ru)

                for di in rec.drive_ids or ([rec.google_drive_id] if rec.google_drive_id else []):
                    if di and di not in matched_existing.drive_ids:
                        matched_existing.drive_ids.append(di)

                # Preserve richest metadata
                if not matched_existing.unit and rec.unit:
                    matched_existing.unit = rec.unit
                if not matched_existing.drive_folder_path and rec.drive_folder_path:
                    matched_existing.drive_folder_path = rec.drive_folder_path
                if not matched_existing.google_drive_id and rec.google_drive_id:
                    matched_existing.google_drive_id = rec.google_drive_id
            else:
                if not rec.sources:
                    rec.sources = [rec.source_site] if rec.source_site else []
                if not rec.source_urls:
                    rec.source_urls = [rec.source_url] if rec.source_url else []
                if not rec.resolved_urls:
                    rec.resolved_urls = [rec.resolved_url] if rec.resolved_url else []
                if not rec.drive_ids:
                    rec.drive_ids = [rec.google_drive_id] if rec.google_drive_id else []
                if not rec.resource_id:
                    if rec.google_drive_id:
                        rec.resource_id = f"gdrive_{rec.google_drive_id}"
                    else:
                        rec.resource_id = f"res_{abs(hash(rec.resolved_url or rec.source_url))}"

                merged_records.append(rec)
                if primary_drive_id:
                    drive_id_map[primary_drive_id] = rec
                if rec.resolved_url:
                    url_map[rec.resolved_url] = rec

        return merged_records

    # =========================================================================
    # PROCESS & EXECUTE PIPELINE
    # =========================================================================

    def process_record(self, record: ManifestRecord, resume: bool = True) -> ManifestRecord:
        """
        Executes full pipeline on a single manifest record:
        Resume Check -> Multi-source Download -> Strict Validation -> Deduplication -> Classification -> Mapping -> Storage.
        """
        print(f"\n--> Processing [{record.source_site}] {record.title}")

        # 1. Check resume status and verify existing file on disk
        if resume:
            existing = None
            if record.google_drive_id:
                existing = self.manifest.get_by_drive_id(record.google_drive_id)
            if not existing and record.sha256:
                existing = self.manifest.get_by_sha256(record.sha256)
            if not existing:
                existing = self.manifest.get_by_source(record.source_site, record.source_url)

            if existing and existing.local_path and os.path.exists(existing.local_path):
                file_size = os.path.getsize(existing.local_path)
                if file_size > 1024:
                    try:
                        with open(existing.local_path, "rb") as f:
                            head = f.read(10)
                            f.seek(max(0, file_size - 2048))
                            tail = f.read()
                        if head.startswith(b"%PDF-") and b"%%EOF" in tail:
                            print(f"    [SKIP] Already verified on disk ({file_size} bytes): {existing.local_path}")
                            for s in record.sources:
                                if s not in existing.sources:
                                    existing.sources.append(s)
                            if not existing.terminal_status:
                                existing.terminal_status = "DOWNLOADED" if existing.download_status != DownloadStatus.DUPLICATE else "DUPLICATE"
                            return self.manifest.add_or_update_record(existing)
                    except Exception:
                        pass

        # 2. Collect candidate URLs for multi-source fallback
        candidate_urls: List[str] = []
        for u in (record.resolved_urls or []) + [record.resolved_url, record.source_url]:
            if u and u not in candidate_urls and not GoogleDriveHandler.is_drive_folder(u):
                candidate_urls.append(u)

        if not candidate_urls:
            record.download_status = DownloadStatus.FAILED
            record.terminal_status = "FAILED"
            record.failure_reason = "No valid download URL could be resolved"
            return self.manifest.add_or_update_record(record)

        # 3. Stream download to temporary file with source fallback
        temp_path = None
        last_error = None

        for download_url in candidate_urls:
            domain = urlparse(download_url).netloc or "default"
            self._sleep_rate_limit(domain)

            print(f"    [DOWNLOADING] {download_url[:80]}...")
            temp_path, last_error = self.downloader.download_to_temp(download_url)
            if not last_error and temp_path:
                break
            print(f"    [FALLBACK] URL failed ({last_error}), trying next candidate source...")

        if last_error or not temp_path:
            print(f"    [FAILED] Download failed for all candidate URLs: {last_error}")
            record.download_status = DownloadStatus.FAILED
            err_lower = (last_error or "").lower()
            if any(term in err_lower for term in ["permission", "auth", "denied", "access", "403", "401"]):
                record.terminal_status = "ACCESS_BLOCKED"
                record.action_required = ActionRequiredItem(
                    source=record.source_site,
                    url=candidate_urls[0],
                    problem=last_error or "Access denied / Authorization required",
                    what_is_needed="Provide public viewing permission or direct download link",
                )
            else:
                record.terminal_status = "FAILED"
            record.failure_reason = last_error or "Download failed across all candidate sources"
            return self.manifest.add_or_update_record(record)

        # 4. Strict PDF Validation
        print("    [VALIDATING] Checking magic bytes and PDF structure...")
        val_result = self.downloader.validate_pdf_file(temp_path)
        if not val_result.is_valid:
            print(f"    [INVALID] Rejected: {val_result.failure_reason}")
            record.download_status = DownloadStatus.INVALID
            record.terminal_status = "INVALID"
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
            record.terminal_status = "DUPLICATE"
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

            if not self.download_only:
                self.ingester.ingest_record(record)
            else:
                record.ingestion_status = "NOT_INGESTED (download-only mode)"

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
        if match_result.canonical_semester:
            record.semester = match_result.canonical_semester

        print(f"    [CURRICULUM] {record.curriculum_status.value} (Course ID: {record.course_id or 'None'}, Sem: {record.semester or 'Unknown'}) - {match_result.notes}")

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
        record.terminal_status = "DOWNLOADED"

        print(f"    [STORED] {stored_path}")

        # 9. Database Ingestion (Strictly bypassed in download-only mode)
        if not self.download_only:
            print("    [INGESTING] Feeding into MarkMint database pipeline...")
            self.ingester.ingest_record(record)
            print(f"    [INGESTED] Status: {record.ingestion_status}")
        else:
            record.ingestion_status = "NOT_INGESTED (download-only mode)"

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
        Constructs a multi-source union graph, then executes downloads and generates the audit report.
        """
        print("=" * 70)
        print("  MARKMINT ACADEMIC RESOURCE CRAWLER PIPELINE")
        print(f"  Source: {source} | Semester: {semester or 'All'} | Limit: {limit or 'No limit'}")
        print("=" * 70)

        sources_crawled = []
        candidates: List[ManifestRecord] = []

        # Phase 1: Exhaustive Discovery & Union Graph Construction
        if source == "all":
            sources_crawled = ["Studique", "TheHelpers"]
            print("\n[Discovery 1/2] Discovering resources from Studique...")
            studique_records = self.discover_studique(
                semester_filter=semester,
                subject_filter=subject,
                max_items=limit,
            )
            print("\n[Discovery 2/2] Discovering resources from The Helpers...")
            helpers_records = self.discover_thehelpers(
                semester_filter=semester,
                subject_filter=subject,
                max_items=limit,
            )
            candidates = self.build_union_graph(studique_records, helpers_records)
        elif source == "studique":
            sources_crawled = ["Studique"]
            candidates = self.discover_studique(
                semester_filter=semester,
                subject_filter=subject,
                max_items=limit,
            )
        elif source == "helpers":
            sources_crawled = ["TheHelpers"]
            candidates = self.discover_thehelpers(
                semester_filter=semester,
                subject_filter=subject,
                max_items=limit,
            )

        print(f"\n[Discovery Complete] Found {len(candidates)} unique candidates across {sources_crawled}.")

        # Phase 2: Processing (Download, Validate, Classify, Map, Ingest)
        target_records = candidates[:limit] if limit else candidates
        processed_count = 0
        try:
            if self.download_only and len(target_records) > 1:
                from concurrent.futures import ThreadPoolExecutor, as_completed
                print(f"\n[Processing] Starting bounded concurrent downloads (4 workers) for {len(target_records)} records...")
                with ThreadPoolExecutor(max_workers=4) as executor:
                    future_to_rec = {
                        executor.submit(self.process_record, rec, resume): rec
                        for rec in target_records
                    }
                    for future in as_completed(future_to_rec):
                        rec = future_to_rec[future]
                        try:
                            future.result()
                            processed_count += 1
                            if processed_count % 25 == 0 or processed_count == len(target_records):
                                print(f"    [Progress] Processed {processed_count}/{len(target_records)} records...")
                        except Exception as e:
                            logger.error("Error processing record %s: %s", rec.title, e)
            else:
                for rec in target_records:
                    self.process_record(rec, resume=resume)
                    processed_count += 1

        except KeyboardInterrupt:
            print("\n[!] Crawl interrupted by user. All progress saved in manifest.")

        # Phase 3: Final Audit Report
        report = self.manifest.generate_audit_report(sources_crawled=sources_crawled)
        return report
