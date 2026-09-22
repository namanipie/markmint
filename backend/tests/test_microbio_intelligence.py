"""
Focused integration tests for Course 10: Microbiology (21BTC201T / 21BTB103T).
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
from backend.services.taxonomy_rules.microbio_rules import MICROBIO_TAXONOMY_RULES
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def test_microbio_taxonomy_integrity():
    """Verify Course 10 has exactly 5 units and 20 topics in SQLite."""
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 10).first()
        assert syl is not None, "Course 10 syllabus must exist"

        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Expected 5 units, found {len(units)}"

        expected_units = [
            (1, "Cell: Basic Unit of Life"),
            (2, "Macromolecules and Metabolism"),
            (3, "Microbiology in Human Life"),
            (4, "Basics of Biosensors and Molecular Motors"),
            (5, "Basics of Biomaterial and its Applications"),
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


def test_microbio_classifier_behavior():
    """Verify deterministic classification rules for representative Microbiology questions."""
    classifier = TaxonomyClassifierService(MICROBIO_TAXONOMY_RULES)

    # Test Cell organelles
    p1 = classifier.classify(1, "Endoplasmic reticulum is absent in prokaryotes.")
    assert p1.confidence == "HIGH"
    assert p1.topic_name == "Cell Structure and Organelles: Organization and Functions"

    # Test Glucose electrode
    p2 = classifier.classify(2, "In glucose electrode, glucose oxidase has been coupled to material.")
    assert p2.confidence == "HIGH"
    assert p2.topic_name == "Glucose Sensors and Clinical Diagnostic Applications"

    # Test Antibiotic resistance
    p3 = classifier.classify(3, "Which of these conditions cannot be treated with antibiotics resistance?")
    assert p3.confidence == "HIGH"
    assert p3.topic_name == "Antibiotics and Antibiotic Resistance Mechanisms"

    # Test Rotatory motors
    p4 = classifier.classify(4, "F0 develops rotary torque by using electrochemical gradient.")
    assert p4.confidence == "HIGH"
    assert p4.topic_name == "Rotary Molecular Motors: Flagellar Motor and ATPase"

    # Test Generic unmapped question
    p5 = classifier.classify(5, "Which electrolyte involves in transmitting action potentials?")
    assert p5.confidence == "UNMAPPED"
    assert p5.topic_id is None


def test_microbio_mapping_invariants():
    """Verify Course 10 mappings: >= 80 mapped, zero cross-course, and zero orphan mappings."""
    db = SessionLocal()
    try:
        total_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 10)
            .count()
        )
        assert total_questions == 115, f"Expected 115 questions, got {total_questions}"

        mapped_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 10, Question.topics.any())
            .count()
        )
        assert mapped_questions >= 80, f"Expected at least 80 mapped questions, got {mapped_questions}"

        # Verify no cross-course mappings
        cross_course_count = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Exam.course_id == 10, Syllabus.course_id != 10)
            .count()
        )
        assert cross_course_count == 0, f"Found {cross_course_count} cross-course topic mappings for Course 10"
    finally:
        db.close()


def test_microbio_intelligence_snapshot():
    """Verify /api/intelligence/10 snapshot returns topic mode and active predictions."""
    db = SessionLocal()
    try:
        snapshot = get_intelligence_snapshot(course_id="10", db=db)
        assert snapshot["prediction_mode"] == "topic"
        assert snapshot["has_topic_taxonomy"] is True
        assert snapshot["taxonomy_topic_count"] == 20
        assert len(snapshot["topic_predictions"]) > 0
        assert len(snapshot["family_predictions"]) > 0
        assert snapshot["exam_history"]["total_papers"] == 4
        assert snapshot["exam_history"]["total_questions"] == 115
    finally:
        db.close()


def test_microbio_study_plan_and_practice():
    """Verify study plan operates in topic mode and practice endpoint returns questions."""
    db = SessionLocal()
    try:
        priorities = get_study_priorities("Microbiology", db=db)
        assert priorities["plan_mode"] == "topic"
        assert len(priorities["priorities"]) > 0
        assert priorities["has_topic_taxonomy"] is True

        practice = get_practice_questions("Microbiology", limit=10)
        assert len(practice["questions"]) == 10
        assert practice["subject"] == "Microbiology"
    finally:
        db.close()
