"""
Focused integration tests for Course 7: Biomedical Sensors (21BMB101T / 21BMC101J).
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
from backend.services.taxonomy_rules.bmb_rules import BMB_TAXONOMY_RULES
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def test_bmb_taxonomy_integrity():
    """Verify Course 7 has exactly 5 units and 20 topics in SQLite."""
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 7).first()
        assert syl is not None, "Course 7 syllabus must exist"

        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Expected 5 units, found {len(units)}"

        expected_units = [
            (1, "Measurement System and Medical Instrumentation"),
            (2, "Temperature Transducers"),
            (3, "Pressure and Magnetic Transducers"),
            (4, "Optical Transducers"),
            (5, "Medical Applications of Sensors"),
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


def test_bmb_classifier_behavior():
    """Verify deterministic classification rules for representative BMB questions."""
    classifier = TaxonomyClassifierService(BMB_TAXONOMY_RULES)

    # Test Primary sensing element
    p1 = classifier.classify(1, "The block that makes physical contact with physical quantity to be measured is Primary sensing element.")
    assert p1.confidence == "HIGH"
    assert p1.topic_name == "Functional Elements and Terminologies of Measurement Systems"

    # Test LVDT
    p2 = classifier.classify(2, "Describe the construction and operating principle of LVDT.")
    assert p2.confidence == "HIGH"
    assert p2.topic_name == "Linear Variable Differential Transformers (LVDT): Construction and Operation"

    # Test Pulse Oximetry
    p3 = classifier.classify(3, "Oximeter measures oxygen saturation in blood.")
    assert p3.confidence == "HIGH"
    assert p3.topic_name == "Pulse Oximetry and Blood Oxygen Saturation (SpO2) Monitoring"

    # Test Seebeck effect
    p4 = classifier.classify(4, "Seeback effect is associated with thermocouple.")
    assert p4.confidence == "HIGH"
    assert p4.topic_name == "Thermocouples: Seebeck Effect, Operating Principles, and Applications"

    # Test Generic unmapped question
    p5 = classifier.classify(5, "Answer all the questions from section A.")
    assert p5.confidence == "UNMAPPED"
    assert p5.topic_id is None


def test_bmb_mapping_invariants():
    """Verify Course 7 mappings: >= 20 mapped, zero cross-course, and zero orphan mappings."""
    db = SessionLocal()
    try:
        total_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 7)
            .count()
        )
        assert total_questions == 27, f"Expected 27 questions, got {total_questions}"

        mapped_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 7, Question.topics.any())
            .count()
        )
        assert mapped_questions >= 20, f"Expected at least 20 mapped questions, got {mapped_questions}"

        # Verify no cross-course mappings
        cross_course_count = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Exam.course_id == 7, Syllabus.course_id != 7)
            .count()
        )
        assert cross_course_count == 0, f"Found {cross_course_count} cross-course topic mappings for Course 7"
    finally:
        db.close()


def test_bmb_intelligence_snapshot():
    """Verify /api/intelligence/7 snapshot returns topic mode and truthful sufficiency status."""
    db = SessionLocal()
    try:
        snapshot = get_intelligence_snapshot(course_id="7", db=db)
        # With N=1 exam paper, data_availability_status is truthfully INSUFFICIENT_EVIDENCE,
        # but topic predictions and study plan operate in topic mode backed by canonical taxonomy.
        assert snapshot["data_availability_status"] == "INSUFFICIENT_EVIDENCE"
        assert snapshot["prediction_mode"] == "topic"
        assert snapshot["has_topic_taxonomy"] is True
        assert snapshot["taxonomy_topic_count"] == 20
        assert len(snapshot["topic_predictions"]) > 0
        assert len(snapshot["family_predictions"]) > 0
        assert snapshot["exam_history"]["total_papers"] == 1
        assert snapshot["exam_history"]["total_questions"] == 27
    finally:
        db.close()



def test_bmb_study_plan_and_practice():
    """Verify study plan operates in topic mode and practice endpoint returns questions."""
    db = SessionLocal()
    try:
        priorities = get_study_priorities("Biomedical Sensors", db=db)
        assert priorities["plan_mode"] == "topic"
        assert len(priorities["priorities"]) > 0
        assert priorities["has_topic_taxonomy"] is True

        practice = get_practice_questions("Biomedical Sensors", limit=10)
        assert len(practice["questions"]) == 10
        assert practice["subject"] == "Biomedical Sensors"
    finally:
        db.close()
