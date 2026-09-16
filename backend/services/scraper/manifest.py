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

            loaded_count = 0
            for item in raw_data:
                record = ManifestRecord.model_validate(item)
                key = self._make_key(record.source_site, record.source_url, record.google_drive_id)
                self.records[key] = record

                if record.sha256:
                    self.sha256_index[record.sha256] = key
                if record.google_drive_id:
                    self.drive_id_index[record.google_drive_id] = key
                loaded_count += 1

            logger.info("Loaded %d manifest records from %s.", loaded_count, self.manifest_path)
        except Exception as e:
            logger.error("Failed to load manifest from %s: %s", self.manifest_path, e)

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
