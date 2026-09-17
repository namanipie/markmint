"""
Crash-resilient Manifest Manager for MarkMint Academic Resource Pipeline.
Maintains persistent records of every discovered, resolved, downloaded,
classified, and ingested academic file. Supports instant checkpointing and --resume.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from .models import (
    ManifestRecord,
    DownloadStatus,
    AuditReport,
    ActionRequiredItem,
    FailureDetail,
    ResourceClassification,
    CurriculumMatchState,
)

logger = logging.getLogger(__name__)


class ManifestManager:
    """Manages persistent JSON manifest with atomic writes and deduplication indices."""

    def __init__(self, manifest_path: str = "data/manifest.json"):
        self.manifest_path = manifest_path
        os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)

        self.records: Dict[str, ManifestRecord] = {}  # key: unique tracking key
        self.sha256_index: Dict[str, str] = {}  # sha256 -> key
        self.drive_id_index: Dict[str, str] = {}  # drive_id -> key

        self.load()

    def _make_key(self, source_site: str, source_url: str, drive_id: Optional[str] = None) -> str:
        if drive_id:
            return f"{source_site}:{drive_id}"
        return f"{source_site}:{source_url}"

    def load(self):
        """Loads manifest from disk and populates lookup indices."""
        if not os.path.exists(self.manifest_path):
            logger.info("No existing manifest found at %s. Initialized empty manifest.", self.manifest_path)
            return

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except FileNotFoundError:
            logger.info("Manifest file not found at %s. Initialized empty manifest.", self.manifest_path)
            return
        except json.JSONDecodeError as e:
            logger.error("Failed to parse manifest JSON from %s: %s", self.manifest_path, e)
            raise

        if not isinstance(raw_data, list):
            raise ValueError(f"Manifest {self.manifest_path} must contain a JSON list")

        references = {
            value
            for item in raw_data
            for value in (item.get("resource_id"), item.get("google_drive_id"))
            if value
        }
        hashes_by_reference: Dict[str, Optional[str]] = {}
        for item in raw_data:
            sha = item.get("sha256")
            if not sha:
                continue
            for ref in (item.get("resource_id"), item.get("google_drive_id")):
                if ref and ref not in hashes_by_reference:
                    hashes_by_reference[ref] = sha

        loaded_count = 0
        for index, item in enumerate(raw_data):
            try:
                normalized_item = self._normalize_legacy_duplicate_reference(
                    item, references, hashes_by_reference
                )
                record = ManifestRecord.model_validate(normalized_item)
            except Exception as e:
                rec_id = item.get("resource_id") or item.get("google_drive_id") or item.get("source_url") or index
                message = f"Manifest record {index} (id={rec_id!r}) failed validation: {e}"
                logger.error(message)
                raise ValueError(message) from e

            key = self._make_key(record.source_site, record.source_url, record.google_drive_id)
            self.records[key] = record

            if record.sha256:
                self.sha256_index[record.sha256] = key
            if record.google_drive_id:
                self.drive_id_index[record.google_drive_id] = key
            loaded_count += 1

        logger.info("Loaded %d manifest records from %s.", loaded_count, self.manifest_path)

    @staticmethod
    def _normalize_legacy_duplicate_reference(
        item: Dict[str, Any],
        references: set[str],
        hashes_by_reference: Dict[str, Optional[str]],
    ) -> Dict[str, Any]:
        """Normalize only verified legacy duplicate references and boolean encodings, preserving their source value."""
        value = item.get("potential_content_duplicate")
        if value is None:
            return item
        if isinstance(value, bool):
            return item

        if isinstance(value, str):
            stripped = value.strip()
            if stripped.lower() in ("true", "1"):
                normalized = dict(item)
                normalized["potential_content_duplicate"] = True
                return normalized
            if stripped.lower() in ("false", "0"):
                normalized = dict(item)
                normalized["potential_content_duplicate"] = False
                return normalized

            if value not in references or not item.get("sha256"):
                raise ValueError(f"unrecognized duplicate reference {value!r}")
            if hashes_by_reference.get(value) != item["sha256"]:
                raise ValueError(
                    f"duplicate reference {value!r} has a different SHA-256 "
                    f"({hashes_by_reference.get(value)} vs {item.get('sha256')})"
                )

            normalized = dict(item)
            normalized["potential_content_duplicate"] = True
            normalized["potential_content_duplicate_reference"] = value
            return normalized

        if isinstance(value, (int, float)):
            if value == 1:
                normalized = dict(item)
                normalized["potential_content_duplicate"] = True
                return normalized
            if value == 0:
                normalized = dict(item)
                normalized["potential_content_duplicate"] = False
                return normalized

        raise ValueError(f"invalid duplicate field value: {value!r} of type {type(value).__name__}")

    def save(self):
        """Atomically saves manifest to disk."""
        temp_path = f"{self.manifest_path}.tmp"
        data = [r.model_dump() for r in self.records.values()]
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.manifest_path)
        except Exception as e:
            logger.error("Failed to save manifest to %s: %s", self.manifest_path, e)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def add_or_update_record(self, record: ManifestRecord) -> ManifestRecord:
        """Adds or updates a record and flushes to disk."""
        key = self._make_key(record.source_site, record.source_url, record.google_drive_id)
        self.records[key] = record

        if record.sha256:
            self.sha256_index[record.sha256] = key
        if record.google_drive_id:
            self.drive_id_index[record.google_drive_id] = key

        self.save()
        return record

    def get_by_sha256(self, sha256_hash: str) -> Optional[ManifestRecord]:
        """Lookup an existing verified record by its SHA-256."""
        key = self.sha256_index.get(sha256_hash)
        if key and key in self.records:
            return self.records[key]
        return None

    def get_by_drive_id(self, drive_id: str) -> Optional[ManifestRecord]:
        """Lookup by Google Drive ID."""
        key = self.drive_id_index.get(drive_id)
        if key and key in self.records:
            return self.records[key]
        return None

    def get_by_source(self, source_site: str, source_url: str) -> Optional[ManifestRecord]:
        """Lookup by source site and source URL."""
        key = self._make_key(source_site, source_url)
        return self.records.get(key)

    def is_already_completed(self, source_site: str, source_url: str, drive_id: Optional[str] = None) -> bool:
        """Check if resource is already downloaded/verified or ingested."""
        if drive_id and drive_id in self.drive_id_index:
            rec = self.records.get(self.drive_id_index[drive_id])
            if rec and rec.download_status in [
                DownloadStatus.DOWNLOADED,
                DownloadStatus.DUPLICATE,
                DownloadStatus.INGESTED,
                DownloadStatus.CLASSIFIED,
                DownloadStatus.UNMAPPED,
            ] and rec.local_path and os.path.exists(rec.local_path):
                return True

        key = self._make_key(source_site, source_url, drive_id)
        rec = self.records.get(key)
        if rec and rec.download_status in [
            DownloadStatus.DOWNLOADED,
            DownloadStatus.DUPLICATE,
            DownloadStatus.INGESTED,
            DownloadStatus.CLASSIFIED,
            DownloadStatus.UNMAPPED,
        ] and rec.local_path and os.path.exists(rec.local_path):
            return True

        return False

    def generate_audit_report(self, sources_crawled: Optional[List[str]] = None) -> AuditReport:
        """Generates comprehensive audit metrics matching requirements."""
        report = AuditReport()
        report.sources_crawled = sources_crawled or list({r.source_site for r in self.records.values()})

        report.resources_discovered = len(self.records)

        seen_sha256 = set()

        for rec in self.records.values():
            if rec.google_drive_id:
                report.files_discovered += 1
            if rec.drive_folder_path:
                report.folders_discovered += 1

            if rec.download_status in [DownloadStatus.DOWNLOADED, DownloadStatus.INGESTED, DownloadStatus.CLASSIFIED, DownloadStatus.UNMAPPED]:
                report.pdfs_downloaded += 1
            elif rec.download_status == DownloadStatus.DUPLICATE:
                report.duplicates += 1
            elif rec.download_status == DownloadStatus.INVALID:
                report.pdfs_invalid += 1
            elif rec.download_status == DownloadStatus.FAILED:
                report.pdfs_failed += 1

            # Classification counts
            if rec.classification == ResourceClassification.PYQ:
                report.pyqs += 1
            elif rec.classification == ResourceClassification.STUDY_MATERIAL:
                report.study_materials += 1
            elif rec.classification == ResourceClassification.UNKNOWN:
                report.unknown_classifications += 1

            # Curriculum status counts
            if rec.curriculum_status == CurriculumMatchState.MATCHED:
                report.matched += 1
            elif rec.curriculum_status == CurriculumMatchState.AMBIGUOUS:
                report.ambiguous += 1
            elif rec.curriculum_status == CurriculumMatchState.UNMATCHED:
                report.unmatched += 1
            elif rec.curriculum_status == CurriculumMatchState.CATALOG_ONLY:
                report.catalog_only += 1

            # Ingestion counts
            if rec.ingestion_status == "INGESTED":
                report.ingested += 1
            elif rec.ingestion_status == "FAILED":
                report.failed_ingestion += 1

            # Action required
            if rec.action_required:
                report.actions_required.append(rec.action_required)

            # Failure details
            if rec.download_status in [DownloadStatus.FAILED, DownloadStatus.INVALID] or rec.failure_reason:
                report.failures.append(
                    FailureDetail(
                        url=rec.resolved_url or rec.source_url,
                        stage=rec.download_status.value,
                        error=rec.failure_reason or "Unknown failure",
                        suggested_resolution="Check manual permissions or retry download",
                    )
                )

        return report
