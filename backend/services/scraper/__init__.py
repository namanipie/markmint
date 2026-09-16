"""
MarkMint Academic Resource Scraper, Crawler, and Ingestion Engine.
"""

# Models
from .models import (
    ResourceClassification,
    CurriculumMatchState,
    DownloadStatus,
    ClassificationResult,
    CurriculumMatchResult,
    ActionRequiredItem,
    FailureDetail,
    ManifestRecord,
    AuditReport,
)

# Core Pipeline Components
from .classifier import ResourceClassifier
from .curriculum_resolver import CurriculumResolver
from .drive_handler import GoogleDriveHandler, GoogleDriveItem
from .downloader import ResourceDownloader, sanitize_filesystem_name, ValidationResult
from .manifest import ManifestManager
from .ingester import CorpusIngester
from .crawler import AcademicResourceCrawler

__all__ = [
    "ResourceClassification",
    "CurriculumMatchState",
    "DownloadStatus",
    "ClassificationResult",
    "CurriculumMatchResult",
    "ActionRequiredItem",
    "FailureDetail",
    "ManifestRecord",
    "AuditReport",
    "ResourceClassifier",
    "CurriculumResolver",
    "GoogleDriveHandler",
    "GoogleDriveItem",
    "ResourceDownloader",
    "sanitize_filesystem_name",
    "ValidationResult",
    "ManifestManager",
    "CorpusIngester",
    "AcademicResourceCrawler",
]
