import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.models.core import (
    Course,
    Exam,
    Section,
    Question,
    Topic,
    Unit,
    Syllabus,
    QuestionFamily,
    QuestionFamilyMembership,
    question_topic,
)
from backend.services.scraper.post_processor import PostIngestionPipeline
from backend.services.intelligence_cache import IntelligenceCacheService


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_post_ingestion_pipeline_end_to_end(test_db):
    # Setup Course 2 (Engineering Chemistry) with syllabus and topics
    course = Course(id=2, name="Engineering Chemistry", code="21CHY101J")
    test_db.add(course)
    test_db.flush()

    syl = Syllabus(course_id=course.id, version="v1")
    test_db.add(syl)
    test_db.flush()

    unit1 = Unit(syllabus_id=syl.id, number=1, name="Electrochemistry")
    test_db.add(unit1)
    test_db.flush()

    t1 = Topic(id=101, unit_id=unit1.id, name="Nernst Equation")
    t2 = Topic(id=102, unit_id=unit1.id, name="Electrochemical Cells")
    test_db.add_all([t1, t2])
    test_db.flush()

    # Pre-existing question family in the same course
    existing_fam = QuestionFamily(
        canonical_name="Derive the Nernst equation for single electrode potential.",
        subject=course.name,
        first_seen_year=2021,
        latest_seen_year=2021,
        repetition_type="singleton",
    )
    test_db.add(existing_fam)
    test_db.commit()

    # Create an Exam with two questions:
    # Q1: matches existing_fam
    # Q2: novel question about corrosion
    exam = Exam(course_id=course.id, year=2023, assessment_type="Cycle Test 1")
    test_db.add(exam)
    test_db.flush()

    sec = Section(exam_id=exam.id, name="Part A")
    test_db.add(sec)
    test_db.flush()

    q1 = Question(
        section_id=sec.id,
        question_number="1",
        original_text="Derive the Nernst equation for single electrode potential.",
    )
    q2 = Question(
        section_id=sec.id,
        question_number="2",
        original_text="Explain sacrificial anode cathodic protection method against galvanic corrosion.",
    )
    test_db.add_all([q1, q2])
    test_db.commit()

    # Seed fake cache entry for course
    valid_payload = {
        "data_availability_status": "AVAILABLE",
        "course": {"id": course.id, "name": course.name},
        "metadata": {"generated_at": "2026-09-24T00:00:00Z"},
        "topics": [],
    }
    IntelligenceCacheService.store_snapshot(
        test_db,
        course_id=course.id,
        assessment_cycle="all",
        track_id=None,
        payload=valid_payload,
    )
    assert IntelligenceCacheService.get_snapshot(test_db, course.id, assessment_cycle="all") is not None

    # Execute PostIngestionPipeline
    pipeline = PostIngestionPipeline(test_db)
    result = pipeline.process_exam(exam.id, course.id)

    assert result["exam_id"] == exam.id
    assert result["course_id"] == course.id
    assert result["families_linked"] == 2
    assert result["cache_invalidated"] >= 1

    # Verify cache was invalidated
    assert IntelligenceCacheService.get_snapshot(test_db, course.id, assessment_cycle="all") is None

    # Verify QuestionFamily linking
    test_db.refresh(q1)
    test_db.refresh(q2)
    test_db.refresh(existing_fam)

    # Q1 joined existing_fam
    assert q1.family_id == existing_fam.id
    assert existing_fam.latest_seen_year == 2023
    assert existing_fam.repetition_type == "exact_repeat"

    # Q2 spawned a new family
    assert q2.family_id is not None
    assert q2.family_id != existing_fam.id
    q2_fam = test_db.query(QuestionFamily).filter(QuestionFamily.id == q2.family_id).first()
    assert q2_fam is not None
    assert q2_fam.first_seen_year == 2023
    assert q2_fam.repetition_type == "singleton"

    # Verify memberships and UNIQUE(question_id) invariant
    mem1 = test_db.query(QuestionFamilyMembership).filter_by(question_id=q1.id).first()
    mem2 = test_db.query(QuestionFamilyMembership).filter_by(question_id=q2.id).first()
    assert mem1 is not None and mem1.family_id == existing_fam.id
    assert mem2 is not None and mem2.family_id == q2_fam.id

    assert test_db.query(QuestionFamilyMembership).count() == 2

    # Idempotency verification: running process_exam again must NOT crash or duplicate
    result_replay = pipeline.process_exam(exam.id, course.id)
    assert result_replay["families_linked"] == 2

    assert test_db.query(QuestionFamilyMembership).count() == 2
    assert test_db.query(QuestionFamily).count() == 2
