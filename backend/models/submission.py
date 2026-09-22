from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship

from backend.core.database import Base


class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ConsistencyStatus(str, enum.Enum):
    CONSISTENT = "CONSISTENT"
    MISMATCH = "MISMATCH"
    UNCERTAIN = "UNCERTAIN"


class PaperSubmission(Base):
    """
    Moderated student paper submission record.
    Preserves raw submissions safely isolated from the production corpus (documents/exams/questions)
    until explicitly reviewed and approved by moderation.
    """
    __tablename__ = "paper_submissions"

    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(64), nullable=False, default="application/pdf")

    # Declared metadata by student
    branch_name = Column(String(120), nullable=True)
    semester = Column(Integer, nullable=True)
    subject_name = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    track_id = Column(Integer, ForeignKey("course_tracks.id"), nullable=True)
    declared_assessment = Column(String(64), nullable=True)  # CT1, CT2, EndSem, Model, etc.

    # Automated extraction and consistency hints
    extracted_text = Column(Text, nullable=True)
    page_count = Column(Integer, default=0)
    detected_year = Column(Integer, nullable=True)
    detected_assessment = Column(String(64), nullable=True)
    detected_course_code = Column(String(64), nullable=True)
    consistency_score = Column(Float, default=0.0)  # 0.0 to 1.0
    consistency_status = Column(String(32), default=ConsistencyStatus.UNCERTAIN.value)
    consistency_notes = Column(Text, nullable=True)

    # Duplicate tracking
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    duplicate_of_submission_id = Column(Integer, ForeignKey("paper_submissions.id"), nullable=True)

    # Provenance & Moderation
    source = Column(String(64), default="STUDENT_SUBMISSION", nullable=False)
    uploader_session_id = Column(String(64), nullable=True, index=True)  # Anonymized session UUID/hash (no PII)
    status = Column(String(32), default=SubmissionStatus.PENDING.value, index=True, nullable=False)
    rejection_reason = Column(Text, nullable=True)

    # Lifecycle timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(64), nullable=True)
    ingested_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

    # Relationships
    course = relationship("Course", foreign_keys=[course_id])
    track = relationship("CourseTrack", foreign_keys=[track_id])
    ingested_document = relationship("Document", foreign_keys=[ingested_document_id])
    duplicate_document = relationship("Document", foreign_keys=[duplicate_of_document_id])
    duplicate_submission = relationship("PaperSubmission", remote_side=[id], foreign_keys=[duplicate_of_submission_id])
