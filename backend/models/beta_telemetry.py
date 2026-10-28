from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from backend.core.database import Base, engine

class BetaEvent(Base):
    """Anonymous telemetry event for beta funnel & friction analysis."""
    __tablename__ = "beta_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    event_name = Column(String(64), index=True, nullable=False)
    route = Column(String(128), nullable=True)
    course_id = Column(Integer, nullable=True)
    course_code = Column(String(32), nullable=True)
    assessment_cycle = Column(String(32), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class BetaFeedback(Base):
    """Anonymous micro-feedback collected after meaningful student interaction."""
    __tablename__ = "beta_feedback"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    useful = Column(Boolean, nullable=False)
    confusion_reason = Column(Text, nullable=True)
    route = Column(String(128), nullable=True)
    course_code = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class BetaError(Base):
    """Lightweight client & server error log strictly stripped of PII and question text."""
    __tablename__ = "beta_errors"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    route = Column(String(128), nullable=True)
    error_type = Column(String(64), nullable=False, index=True)
    message = Column(Text, nullable=True)
    context_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class StudentExamAnnouncement(Base):
    """
    Student crowd-sourced exam scope announcement.
    Allows students to report upcoming exam portions, target units, and batch
    timetables to calibrate MarkMint predictions and question generation for their section.
    """
    __tablename__ = "student_exam_announcements"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, nullable=True, index=True)
    course_code = Column(String(64), nullable=True, index=True)
    course_name = Column(String(255), nullable=False)
    exam_type = Column(String(64), nullable=False)  # CT1, CT2, MODEL, SURPRISE, ENDSEM, OTHER
    exam_title = Column(String(128), nullable=True)
    units = Column(JSON, nullable=False)  # List[int], e.g. [1, 2]
    batch_department = Column(String(128), nullable=True)
    announced_date = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    session_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# Ensure tables exist safely
try:
    Base.metadata.create_all(bind=engine, tables=[
        BetaEvent.__table__,
        BetaFeedback.__table__,
        BetaError.__table__,
        StudentExamAnnouncement.__table__
    ], checkfirst=True)
except Exception:
    pass
