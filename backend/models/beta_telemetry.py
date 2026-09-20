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


# Ensure tables exist
Base.metadata.create_all(bind=engine, tables=[
    BetaEvent.__table__,
    BetaFeedback.__table__,
    BetaError.__table__
])
