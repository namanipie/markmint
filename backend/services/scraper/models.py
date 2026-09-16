"""
Data models for the MarkMint academic resource crawler, classifier, manifest, and ingestion pipeline.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ResourceClassification(str, Enum):
    """Deterministic classification categories."""
    PYQ = "PYQ"
    STUDY_MATERIAL = "STUDY_MATERIAL"
    SYLLABUS = "SYLLABUS"
    ASSIGNMENT = "ASSIGNMENT"
    LAB = "LAB"
    REFERENCE = "REFERENCE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class CurriculumMatchState(str, Enum):
    """States for canonical curriculum resolution."""
    MATCHED = "MATCHED"
    AMBIGUOUS = "AMBIGUOUS"
    UNMATCHED = "UNMATCHED"
    CATALOG_ONLY = "CATALOG_ONLY"


class DownloadStatus(str, Enum):
    """Processing & download lifecycle statuses."""
    DISCOVERED = "DISCOVERED"
    RESOLVED = "RESOLVED"
    DOWNLOADED = "DOWNLOADED"
    DUPLICATE = "DUPLICATE"
    INVALID = "INVALID"
    FAILED = "FAILED"
    CLASSIFIED = "CLASSIFIED"
    INGESTED = "INGESTED"
    UNMAPPED = "UNMAPPED"
    SKIPPED = "SKIPPED"


class ClassificationResult(BaseModel):
    """Result of deterministic document classification."""
    category: ResourceClassification = ResourceClassification.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)
    extracted_year: Optional[int] = None
    assessment_type: Optional[str] = None


class CurriculumMatchResult(BaseModel):
    """Result of subject to curriculum resolution."""
    status: CurriculumMatchState = CurriculumMatchState.UNMATCHED
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    canonical_code: Optional[str] = None
    curriculum_mapping_id: Optional[int] = None
    notes: Optional[str] = None


class ActionRequiredItem(BaseModel):
    """Report item when a remote resource cannot be accessed without user intervention."""
    source: str
    url: str
    problem: str
    what_is_needed: str


class FailureDetail(BaseModel):
    """Details of a failed download or processing stage."""
    url: str
    stage: str
    error: str
    retry_count: int = 0
    suggested_resolution: str = ""


class ManifestRecord(BaseModel):
    """
    Comprehensive manifest record tracking each discovered academic asset.
    Preserves all provenance, filesystem paths, hashes, and statuses.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    source_site: str = Field(description="The source site (e.g. 'Studique', 'TheHelpers')")
    source_url: str = Field(description="URL where resource was referenced or discovered")
    resolved_url: Optional[str] = Field(default=None, description="Direct download / target URL")
    semester: Optional[str] = Field(default=None, description="Semester context (e.g. '1', '2')")
    subject: Optional[str] = Field(default=None, description="Subject / Course title from navigation context")
    unit: Optional[str] = Field(default=None, description="Unit context if available (e.g. 'Unit 1')")
    title: str = Field(description="Resource title")
    resource_type: Optional[str] = Field(default=None, description="Original source type (e.g. 'ppt', 'pyq')")
    google_drive_id: Optional[str] = Field(default=None, description="Google Drive file or folder ID")
    drive_folder_path: Optional[str] = Field(default=None, description="Preserved hierarchy in Google Drive folder")
    download_status: DownloadStatus = Field(default=DownloadStatus.DISCOVERED)
    local_path: Optional[str] = Field(default=None, description="Path to verified file on local disk")
    sha256: Optional[str] = Field(default=None, description="SHA-256 hash of downloaded file")
    file_size: Optional[int] = Field(default=None, description="Size in bytes")
    classification: Optional[ResourceClassification] = None
    classification_confidence: Optional[float] = None
    classification_reasons: List[str] = Field(default_factory=list)
    extracted_year: Optional[int] = None
    assessment_type: Optional[str] = None
    curriculum_status: Optional[CurriculumMatchState] = None
    course_id: Optional[int] = None
    curriculum_mapping_id: Optional[int] = None
    ingestion_status: Optional[str] = None
    failure_reason: Optional[str] = None
    action_required: Optional[ActionRequiredItem] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditReport(BaseModel):
    """Final audit report capturing the full crawl & ingestion results."""
    sources_crawled: List[str] = Field(default_factory=list)
    pages_visited: int = 0
    resources_discovered: int = 0
    files_discovered: int = 0
    folders_discovered: int = 0
    pdfs_downloaded: int = 0
    pdfs_failed: int = 0
    pdfs_invalid: int = 0
    duplicates: int = 0
    pyqs: int = 0
    study_materials: int = 0
    unknown_classifications: int = 0
    matched: int = 0
    ambiguous: int = 0
    unmatched: int = 0
    catalog_only: int = 0
    ingested: int = 0
    failed_ingestion: int = 0
    actions_required: List[ActionRequiredItem] = Field(default_factory=list)
    failures: List[FailureDetail] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
