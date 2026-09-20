from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean, DateTime, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.core.database import Base


class CourseAssessmentPlan(Base):
    """
    Authoritative assessment plan for a course under a specific regulation year.
    Specifies how formative (CT/CLA/quizzes) and summative (EndSem) components are structured.
    """
    __tablename__ = "course_assessment_plans"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    track_id = Column(Integer, ForeignKey("course_tracks.id", ondelete="CASCADE"), nullable=True, index=True)
    regulation_year = Column(Integer, nullable=True)
    source_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    source_title = Column(String, nullable=True)
    version = Column(String, nullable=False, default="1.0")
    provenance = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course")
    source_document = relationship("Document")
    components = relationship("AssessmentComponent", back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("course_id", "track_id", "regulation_year", "version", name="uq_course_track_assessment_plan"),
    )


class AssessmentComponent(Base):
    """
    Specific assessment component for a course (e.g. CT1, CT2, ENDSEM, FT2, FT IV, CT3).
    Binds the raw examination labels, semantic role, student-facing interpretation, and marks.
    """
    __tablename__ = "assessment_components"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("course_assessment_plans.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    
    code = Column(String, nullable=False, index=True)  # e.g. "CT1", "CT2", "ENDSEM", "FT_IV", "CT3"
    canonical_label = Column(String, nullable=False)   # e.g. "Cycle Test 1", "Formative Assessment IV"
    student_label = Column(String, nullable=False)     # e.g. "CT1", "CT2", "End Semester"
    role = Column(String, nullable=False)              # e.g. "CYCLE_TEST", "FORMATIVE_TEST", "SUMMATIVE_EXAM", "MODEL_TEST"
    sequence = Column(Integer, default=1)
    marks = Column(Float, nullable=True)
    raw_labels = Column(JSON, nullable=True)           # List of raw strings mapped to this component
    provenance = Column(JSON, nullable=True)

    # Relationships
    plan = relationship("CourseAssessmentPlan", back_populates="components")
    course = relationship("Course")
    coverages = relationship("AssessmentCoverage", back_populates="component", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("plan_id", "code", name="uq_plan_component_code"),
        Index("ix_course_component_role", "course_id", "role"),
    )


class AssessmentCoverage(Base):
    """
    Authoritative syllabus scope for an assessment component.
    Maps which units and topics are in-scope or out-of-scope.
    """
    __tablename__ = "assessment_coverages"

    id = Column(Integer, primary_key=True, index=True)
    assessment_component_id = Column(Integer, ForeignKey("assessment_components.id"), nullable=False, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True, index=True)
    coverage_type = Column(String, nullable=False, default="IN_SCOPE")  # "IN_SCOPE", "OUT_OF_SCOPE", "OPTIONAL"
    provenance = Column(JSON, nullable=True)

    # Relationships
    component = relationship("AssessmentComponent", back_populates="coverages")
    unit = relationship("Unit")
    topic = relationship("Topic")

    __table_args__ = (
        Index("ix_coverage_component_unit", "assessment_component_id", "unit_id"),
        Index("ix_coverage_component_topic", "assessment_component_id", "topic_id"),
    )
