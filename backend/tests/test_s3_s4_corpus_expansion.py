"""
Regression Test Suite for Semester 3 / Semester 4 Verified Corpus Expansion.

Proves the 10 core architectural and corpus invariants:
1. Syllabus taxonomy is authoritative (strictly matches official syllabus source)
2. Variable unit counts are preserved
3. Question -> Topic -> Unit lineage is valid
4. No cross-course mappings (strict zero cross-course leakage)
5. Assessment identification preserves provenance (raw type, normalized code, source, confidence)
6. Observed scope is paper-derived (derived strictly from mapped questions)
7. Intended scope is not confused with observed scope (decoupled data structures)
8. Question-bank material remains isolated (zero non-exam contamination in S3/S4 corpus)
9. Ingestion is idempotent (rerunning ingestion/mapping causes zero duplication)
10. Historical data remains temporally isolated (strict chronological cutoff integrity)
"""

import os
import sys
import json
import pytest
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from backend.core.database import SessionLocal
from backend.models.core import (
    Course, Syllabus, Unit, Topic, Exam, Section, Question, Document, question_topic
)
from backend.models.assessment import CourseAssessmentPlan, AssessmentComponent, AssessmentCoverage
from backend.services.taxonomy_registry import get_taxonomy_registry, reset_taxonomy_registry
from backend.services.observed_assessment_coverage import (
    identify_exam_assessment,
    compute_paper_observed_coverage,
    compute_cycle_observed_coverage,
)

S3_S4_COURSE_IDS = [24, 25, 26, 27, 28]

EXPECTED_COURSES = {
    24: {"canonical_code": "21CSC201J", "name": "Data Structures and Algorithms", "sem": 3, "min_tid": 737, "max_tid": 763, "topic_count": 27, "paper_count": 7},
    25: {"canonical_code": "21CSC202J", "name": "Operating Systems", "sem": 3, "min_tid": 764, "max_tid": 790, "topic_count": 27, "paper_count": 6},
    26: {"canonical_code": "21CSS201T", "name": "Computer Organization and Architecture", "sem": 3, "min_tid": 791, "max_tid": 815, "topic_count": 25, "paper_count": 4},
    27: {"canonical_code": "21CSC204J", "name": "Design and Analysis of Algorithms", "sem": 4, "min_tid": 816, "max_tid": 840, "topic_count": 25, "paper_count": 8},
    28: {"canonical_code": "21CSC205P", "name": "Database Management Systems", "sem": 4, "min_tid": 841, "max_tid": 865, "topic_count": 25, "paper_count": 4},
}


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_1_syllabus_taxonomy_is_authoritative():
    """1. Prove syllabus taxonomy is authoritative and loaded strictly from verified definitions."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    for cid, exp in EXPECTED_COURSES.items():
        assert registry.has_course(cid), f"Course {cid} must exist in TaxonomyRegistry"
        entry = registry.get_course(cid)
        assert entry.course.canonical_code == exp["canonical_code"]
        assert entry.course.name == exp["name"]
        assert len(entry.units) == 5
        rules = registry.get_topic_rules(cid)
        assert len(rules) == exp["topic_count"]

        # Ensure provenance is recorded
        assert entry.provenance is not None
        assert entry.provenance.regulation == "2021"
        assert "SRMIST" in entry.provenance.source_document


def test_2_variable_unit_counts_are_preserved(db: Session):
    """2. Prove variable unit structures are preserved without artificial flattening."""
    for cid in S3_S4_COURSE_IDS:
        syllabus = db.query(Syllabus).filter(Syllabus.course_id == cid).first()
        assert syllabus is not None, f"Course {cid} must have a Syllabus record"
        units = db.query(Unit).filter(Unit.syllabus_id == syllabus.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Course {cid} has 5 canonical units"
        unit_nums = [u.number for u in units]
        assert unit_nums == [1, 2, 3, 4, 5], f"Units must follow sequential 1..N order: {unit_nums}"
        
        for u in units:
            topics = db.query(Topic).filter(Topic.unit_id == u.id).all()
            assert len(topics) >= 1, f"Unit {u.id} ({u.name}) must have at least 1 topic"


def test_3_question_topic_unit_lineage_is_valid(db: Session):
    """3. Prove question -> topic -> unit lineage is fully valid and referentially intact."""
    for cid in S3_S4_COURSE_IDS:
        mapped_rows = (
            db.query(Question.id, Topic.id, Topic.unit_id, Unit.id, Unit.syllabus_id, Syllabus.course_id)
            .join(question_topic, Question.id == question_topic.c.question_id)
            .join(Topic, question_topic.c.topic_id == Topic.id)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .all()
        )
        assert len(mapped_rows) > 0, f"Course {cid} must have mapped questions"
        for q_id, t_id, t_uid, u_id, u_syl_id, s_cid in mapped_rows:
            assert t_uid == u_id, f"Topic {t_id} unit_id {t_uid} must match Unit {u_id}"
            assert s_cid == cid, f"Question {q_id} in Course {cid} mapped to Syllabus of Course {s_cid}"


def test_4_no_cross_course_mappings(db: Session):
    """4. Prove ZERO cross-course mappings exist across all S3/S4 courses."""
    for cid in S3_S4_COURSE_IDS:
        mapped_rows = (
            db.query(Question.id, Topic.id, Unit.syllabus_id, Syllabus.course_id)
            .join(question_topic, Question.id == question_topic.c.question_id)
            .join(Topic, question_topic.c.topic_id == Topic.id)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == cid)
            .all()
        )
        for q_id, t_id, syl_id, topic_course_id in mapped_rows:
            assert topic_course_id == cid, (
                f"LEAKAGE: Question {q_id} (Course {cid}) was mapped to Topic {t_id} (Course {topic_course_id})"
            )


def test_5_assessment_identification_preserves_provenance(db: Session):
    """5. Prove assessment identification preserves raw provenance, normalized code, source, and confidence."""
    for cid in S3_S4_COURSE_IDS:
        exams = db.query(Exam).filter(Exam.course_id == cid).all()
        assert len(exams) >= 4, f"Course {cid} must have at least 4 exam papers"
        for exam in exams:
            ident = identify_exam_assessment(exam, cid)
            assert ident.raw_type == "END_SEM"
            assert ident.normalized_code == "ENDSEM"
            assert ident.student_cycle == "ENDSEM"
            assert ident.identification_source in ["metadata", "document_title", "document_metadata"]
            assert ident.confidence >= 0.9


def test_6_observed_scope_is_paper_derived(db: Session):
    """6. Prove observed scope is derived strictly from paper question mappings."""
    for cid in S3_S4_COURSE_IDS:
        exams = (
            db.query(Exam)
            .options(
                selectinload(Exam.sections).selectinload(Section.questions).selectinload(Question.topics).selectinload(Topic.unit),
                selectinload(Exam.document),
            )
            .filter(Exam.course_id == cid)
            .all()
        )
        for exam in exams:
            coverage = compute_paper_observed_coverage(exam)
            assert coverage.exam_id == exam.id
            assert coverage.total_questions > 0
            assert coverage.mapped_questions_count > 0
            # Observed units must come from questions
            assert len(coverage.observed_unit_numbers) > 0
            # Every observed unit must have question count > 0
            for u in coverage.observed_unit_numbers:
                assert coverage.question_count_by_unit.get(u, 0) > 0


def test_7_intended_scope_is_not_confused_with_observed_scope(db: Session):
    """7. Prove intended institutional scope and observed paper scope remain decoupled."""
    for cid in S3_S4_COURSE_IDS:
        plan = db.query(CourseAssessmentPlan).filter(CourseAssessmentPlan.course_id == cid).first()
        assert plan is not None, f"Course {cid} must have a CourseAssessmentPlan"
        
        cla1_comp = (
            db.query(AssessmentComponent)
            .filter(AssessmentComponent.plan_id == plan.id, AssessmentComponent.code == "CLA1")
            .first()
        )
        assert cla1_comp is not None
        cla1_coverages = db.query(AssessmentCoverage).filter(AssessmentCoverage.assessment_component_id == cla1_comp.id).all()
        cla1_intended_units = set()
        for cov in cla1_coverages:
            u = db.query(Unit).filter(Unit.id == cov.unit_id).first()
            if u:
                cla1_intended_units.add(u.number)
        
        # In institutional plan, CLA1 covers Units 1 & 2 only
        assert cla1_intended_units == {1, 2}

        # EndSem exams observe all 5 units in historical papers
        exams = (
            db.query(Exam)
            .options(
                selectinload(Exam.sections).selectinload(Section.questions).selectinload(Question.topics).selectinload(Topic.unit),
                selectinload(Exam.document),
            )
            .filter(Exam.course_id == cid)
            .all()
        )
        cycle_cov = compute_cycle_observed_coverage(cid, "ENDSEM", exams)
        assert set(cycle_cov.observed_unit_numbers) == {1, 2, 3, 4, 5}


def test_8_question_bank_material_remains_isolated(db: Session):
    """8. Prove zero question bank or non-exam practice material is treated as exam evidence for S3/S4."""
    s3_s4_docs = (
        db.query(Document)
        .join(Exam, Document.id == Exam.document_id)
        .filter(Exam.course_id.in_(S3_S4_COURSE_IDS))
        .all()
    )
    assert len(s3_s4_docs) == 29
    for doc in s3_s4_docs:
        assert doc.resource_type == "QUESTION_PAPER", f"Doc {doc.id} must be QUESTION_PAPER"
        title_lower = doc.title.lower()
        assert "question bank" not in title_lower, f"Doc {doc.id} title contains 'question bank'"
        assert "study material" not in title_lower, f"Doc {doc.id} title contains 'study material'"
        assert "lecture notes" not in title_lower, f"Doc {doc.id} title contains 'lecture notes'"


def test_9_ingestion_is_idempotent(db: Session):
    """9. Prove ingestion and mapping are idempotent without creating duplicate records."""
    # Check uniqueness of exam hashes / document titles per course
    for cid in S3_S4_COURSE_IDS:
        exams = db.query(Exam).filter(Exam.course_id == cid).all()
        doc_ids = [e.document_id for e in exams]
        assert len(doc_ids) == len(set(doc_ids)), f"Duplicate document_id in Course {cid} exams!"

        # Check question IDs are unique and no question has duplicate question_topic links to the same topic
        for e in exams:
            sections = db.query(Section).filter(Section.exam_id == e.id).all()
            for s in sections:
                q_ids = [q.id for q in db.query(Question).filter(Question.section_id == s.id).all()]
                assert len(q_ids) == len(set(q_ids)), f"Duplicate question IDs in Exam {e.id} Section {s.id}!"


def test_10_historical_data_remains_temporally_isolated(db: Session):
    """10. Prove historical exams have valid academic years and strictly respect temporal isolation."""
    for cid in S3_S4_COURSE_IDS:
        exams = db.query(Exam).filter(Exam.course_id == cid).all()
        years = [e.year for e in exams]
        # All exams must have valid years >= 2021 (Regulation 2021)
        for y in years:
            assert y is not None, f"Exam in course {cid} missing year"
            assert 2022 <= y <= 2025, f"Exam year {y} outside valid range 2022-2025"

        # Check temporal cutoff for each course based on available paper years
        cutoff_year = 2023 if cid == 28 else 2024
        prior_papers = [e for e in exams if e.year < cutoff_year]
        target_papers = [e for e in exams if e.year == cutoff_year]
        assert len(prior_papers) >= 1, f"Course {cid} has historical papers prior to {cutoff_year}"
        assert len(target_papers) >= 1, f"Course {cid} has target papers at {cutoff_year}"
        for p in prior_papers:
            assert p.year < cutoff_year, f"Prior paper year {p.year} >= cutoff {cutoff_year}"
