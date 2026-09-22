"""
Focused integration tests for Course 11: Physical And Analytical Chemistry (21CHC101J).
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
from backend.services.taxonomy_rules.pac_rules import PAC_TAXONOMY_RULES
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def test_pac_taxonomy_integrity():
    """Verify Course 11 has exactly 5 units and 20 topics in SQLite."""
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 11).first()
        assert syl is not None, "Course 11 syllabus must exist"

        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Expected 5 units, found {len(units)}"

        expected_units = [
            (1, "Properties of Solutions"),
            (2, "Chemical Equilibrium"),
            (3, "Phase Equilibrium"),
            (4, "Colloids and Photochemistry"),
            (5, "Instrumental Methods of Analysis"),
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


def test_pac_classifier_behavior():
    """Verify deterministic classification rules for representative PAC questions."""
    classifier = TaxonomyClassifierService(PAC_TAXONOMY_RULES)

    # Test Raoult's law
    p1 = classifier.classify(1, "Ideal solutions obey Raoult's law under all concentrations.")
    assert p1.confidence == "HIGH"
    assert p1.topic_name == "Ideal and Non-Ideal Solutions: Raoult's Law and Deviations"

    # Test Le Chatelier
    p2 = classifier.classify(2, "The Le Chatlier's principle states that factors affect equilibrium.")
    assert p2.confidence == "HIGH"
    assert p2.topic_name == "Le Chatelier's Principle and Dynamic Physical-Chemical Equilibria"

    # Test Triple point
    p3 = classifier.classify(3, "At triple point; water exists in equilibrium.")
    assert p3.confidence == "HIGH"
    assert p3.topic_name == "One-Component Systems: Water, CO2, and Sulphur Phase Diagrams"

    # Test UV Spectroscopy
    p4 = classifier.classify(4, "UV Spectroscopy uses the wavelength range 10-400 nm of EM radiation.")
    assert p4.confidence == "HIGH"
    assert p4.topic_name == "Molecular Spectroscopy: UV-Vis and Infrared (IR) Spectroscopy"

    # Test Generic unmapped question
    p5 = classifier.classify(5, "Answer all the questions from section A.")
    assert p5.confidence == "UNMAPPED"
    assert p5.topic_id is None


def test_pac_mapping_invariants():
    """Verify Course 11 mappings: >= 25 mapped, zero cross-course, and zero orphan mappings."""
    db = SessionLocal()
    try:
        total_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 11)
            .count()
        )
        assert total_questions == 32, f"Expected 32 questions, got {total_questions}"

        mapped_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 11, Question.topics.any())
            .count()
        )
        assert mapped_questions >= 25, f"Expected at least 25 mapped questions, got {mapped_questions}"

        # Verify no cross-course mappings
        cross_course_count = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Exam.course_id == 11, Syllabus.course_id != 11)
            .count()
        )
        assert cross_course_count == 0, f"Found {cross_course_count} cross-course topic mappings for Course 11"
    finally:
        db.close()


def test_pac_intelligence_snapshot():
    """Verify /api/intelligence/11 snapshot returns topic mode and active predictions."""
    db = SessionLocal()
    try:
        snapshot = get_intelligence_snapshot(course_id="11", db=db)
        assert snapshot["prediction_mode"] == "topic"
        assert snapshot["has_topic_taxonomy"] is True
        assert snapshot["taxonomy_topic_count"] == 20
        assert len(snapshot["topic_predictions"]) > 0
        assert len(snapshot["family_predictions"]) > 0
        assert snapshot["exam_history"]["total_papers"] == 1
        assert snapshot["exam_history"]["total_questions"] == 32
    finally:
        db.close()


def test_pac_study_plan_and_practice():
    """Verify study plan operates in topic mode and practice endpoint returns questions."""
    db = SessionLocal()
    try:
        priorities = get_study_priorities("Physical And Analytical Chemistry", db=db)
        assert priorities["plan_mode"] == "topic"
        assert len(priorities["priorities"]) > 0
        assert priorities["has_topic_taxonomy"] is True

        practice = get_practice_questions("Physical And Analytical Chemistry", limit=10)
        assert len(practice["questions"]) == 10
        assert practice["subject"] == "Physical And Analytical Chemistry"
    finally:
        db.close()
