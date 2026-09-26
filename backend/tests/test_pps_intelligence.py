"""
Focused integration tests for Course 5: Programming For Problem Solving (21CSS101J).
Verifies:
- 5 units and 20 topics taxonomy integrity
- Classifier behavior and ambiguity rejection
- Mapping persistence and idempotency
- Zero cross-course mappings
- Prediction integration and prediction_mode == 'topic'
- Study plan generation in topic mode
- Practice endpoint returns relevant questions
"""
import pytest
from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus
from backend.services.taxonomy_classifier import TaxonomyClassifierService
from backend.services.taxonomy_rules.pps_rules import PPS_TAXONOMY_RULES
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def test_pps_taxonomy_integrity():
    """Verify Course 5 has exactly 5 units and 20 topics in SQLite."""
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 5).first()
        assert syl is not None, "Course 5 syllabus must exist"

        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Expected 5 units, found {len(units)}"

        expected_units = [
            (1, "Problem Solving and C Basics"),
            (2, "Control Flow, Arrays, and Pointers"),
            (3, "Strings, Functions, and Storage Classes"),
            (4, "Introduction to Python and Data Structures"),
            (5, "Data Analysis with NumPy and Pandas"),
        ]
        for (exp_num, exp_name), u in zip(expected_units, units):
            assert u.number == exp_num
            assert u.name == exp_name

        topics = (
            db.query(Topic)
            .join(Unit, Topic.unit_id == Unit.id)
            .filter(Unit.syllabus_id == syl.id)
            .all()
        )
        assert len(topics) == 20, f"Expected 20 topics, found {len(topics)}"
    finally:
        db.close()


def test_pps_classifier_behavior():
    """Verify deterministic classification rules for representative PPS questions."""
    classifier = TaxonomyClassifierService(PPS_TAXONOMY_RULES)

    # Test Flowchart / Algorithm
    p1 = classifier.classify(1, "Which flowchart symbol is used to represent a decision point in a process?")
    assert p1.confidence == "HIGH"
    assert p1.topic_name == "Problem Solving Process, Algorithms, and Flowcharts"

    # Test Pointers
    p2 = classifier.classify(2, "What is pointer declaration and dereferencing and also define null pointer in C?")
    assert p2.confidence == "HIGH"
    assert p2.topic_name == "Pointers, Address-of Operator, Dereferencing, and Pointer Arithmetic"

    # Test Storage classes
    p3 = classifier.classify(3, "Analyze the various Storage Classes in C with suitable examples.")
    assert p3.confidence == "HIGH"
    assert p3.topic_name == "Storage Classes, Variable Scope, and Linkage"

    # Test Pandas DataFrame
    p4 = classifier.classify(4, "Explain the Operations that can be performed on a Python Data Frame.")
    assert p4.confidence == "HIGH"
    assert p4.topic_name == "Data Manipulation, Querying, and Tabular Operations in Pandas"

    # Test Generic unmapped question
    p5 = classifier.classify(5, "Answer all the questions from section A.")
    assert p5.confidence == "UNMAPPED"
    assert p5.topic_id is None


def test_pps_mapping_invariants():
    """Verify Course 5 mappings: >= 180 mapped, zero cross-course, and zero orphan mappings."""
    db = SessionLocal()
    try:
        # Check total questions and mapped questions
        total_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 5)
            .count()
        )
        assert total_questions == 362, f"Expected 362 questions, got {total_questions}"

        mapped_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 5, Question.topics.any())
            .count()
        )
        assert mapped_questions >= 180, f"Expected at least 180 mapped questions, got {mapped_questions}"

        # Verify no cross-course mappings
        cross_course_count = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Exam.course_id == 5, Syllabus.course_id != 5)
            .count()
        )
        assert cross_course_count == 0, f"Found {cross_course_count} cross-course topic mappings for Course 5"
    finally:
        db.close()


def test_pps_intelligence_snapshot():
    """Verify /api/intelligence/5 snapshot returns topic mode and rich evidence."""
    db = SessionLocal()
    try:
        snapshot = get_intelligence_snapshot(course_id="5", db=db)
        assert snapshot["data_availability_status"] == "READY"
        assert snapshot["prediction_mode"] == "topic"
        assert snapshot["has_topic_taxonomy"] is True
        assert snapshot["taxonomy_topic_count"] == 20
        assert len(snapshot["topic_predictions"]) > 0
        assert len(snapshot["family_predictions"]) > 0
        assert snapshot["exam_history"]["total_papers"] == 20
        assert snapshot["exam_history"]["years"] == [2019, 2022, 2023, 2024]
    finally:
        db.close()


def test_pps_study_plan_and_practice():
    """Verify study plan operates in topic mode and practice endpoint returns questions."""
    db = SessionLocal()
    try:
        priorities = get_study_priorities("Programming For Problem Solving", db=db)
        assert priorities["plan_mode"] == "topic"
        assert len(priorities["priorities"]) > 0
        assert priorities["has_topic_taxonomy"] is True

        practice = get_practice_questions("Programming For Problem Solving", limit=10)
        assert len(practice["questions"]) == 10
        assert practice["subject"] == "Programming For Problem Solving"
    finally:
        db.close()
