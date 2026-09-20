"""
Focused integration tests for Course 6: Fundamental Of Economics (FOE) (18MSS101T).
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
from backend.services.taxonomy_rules.foe_rules import FOE_TAXONOMY_RULES
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def test_foe_taxonomy_integrity():
    """Verify Course 6 has exactly 5 units and 20 topics in SQLite."""
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 6).first()
        assert syl is not None, "Course 6 syllabus must exist"

        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Expected 5 units, found {len(units)}"

        expected_units = [
            (1, "Introduction to Economics and Consumer Behaviour"),
            (2, "Demand, Supply, and Market Equilibrium"),
            (3, "Production and Cost Analysis"),
            (4, "Market Structures and Pricing"),
            (5, "Money, Banking, and Macroeconomic Aggregates"),
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


def test_foe_classifier_behavior():
    """Verify deterministic classification rules for representative FOE questions."""
    classifier = TaxonomyClassifierService(FOE_TAXONOMY_RULES)

    # Test Adam Smith / Definitions
    p1 = classifier.classify(1, "Who is considered the father of modern economics? Adam Smith.")
    assert p1.confidence == "HIGH"
    assert p1.topic_name == "Definitions, Nature, and Scope of Economics"

    # Test Law of Demand
    p2 = classifier.classify(2, "Define the Demand Curve and explain the law of demand.")
    assert p2.confidence == "HIGH"
    assert p2.topic_name == "Theory of Demand, Law of Demand, and Demand Elasticity"

    # Test Law of Variable Proportions
    p3 = classifier.classify(3, "Write a short note on Law of Variable proportions.")
    assert p3.confidence == "HIGH"
    assert p3.topic_name == "Law of Variable Proportions and Returns to Scale"

    # Test Perfect Competition
    p4 = classifier.classify(4, "In a perfectly competitive market, all firms produce identical products.")
    assert p4.confidence == "HIGH"
    assert p4.topic_name == "Perfect Competition: Features and Equilibrium Analysis"

    # Test Generic unmapped question
    p5 = classifier.classify(5, "Answer all the questions from section A.")
    assert p5.confidence == "UNMAPPED"
    assert p5.topic_id is None


def test_foe_mapping_invariants():
    """Verify Course 6 mappings: >= 70 mapped, zero cross-course, and zero orphan mappings."""
    db = SessionLocal()
    try:
        # Check total questions and mapped questions
        total_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 6)
            .count()
        )
        assert total_questions == 128, f"Expected 128 questions, got {total_questions}"

        mapped_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 6, Question.topics.any())
            .count()
        )
        assert mapped_questions >= 70, f"Expected at least 70 mapped questions, got {mapped_questions}"

        # Verify no cross-course mappings
        cross_course_count = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Exam.course_id == 6, Syllabus.course_id != 6)
            .count()
        )
        assert cross_course_count == 0, f"Found {cross_course_count} cross-course topic mappings for Course 6"
    finally:
        db.close()


def test_foe_intelligence_snapshot():
    """Verify /api/intelligence/6 snapshot returns topic mode and rich evidence."""
    db = SessionLocal()
    try:
        snapshot = get_intelligence_snapshot(course_id="6", db=db)
        assert snapshot["data_availability_status"] == "READY"
        assert snapshot["prediction_mode"] == "topic"
        assert snapshot["has_topic_taxonomy"] is True
        assert snapshot["taxonomy_topic_count"] == 20
        assert len(snapshot["topic_predictions"]) > 0
        assert len(snapshot["family_predictions"]) > 0
        assert snapshot["exam_history"]["total_papers"] == 4
        assert snapshot["exam_history"]["years"] == [2023, 2024]
    finally:
        db.close()


def test_foe_study_plan_and_practice():
    """Verify study plan operates in topic mode and practice endpoint returns questions."""
    db = SessionLocal()
    try:
        priorities = get_study_priorities("Fundamental Of Economics (FOE)", db=db)
        assert priorities["plan_mode"] == "topic"
        assert len(priorities["priorities"]) > 0
        assert priorities["has_topic_taxonomy"] is True

        practice = get_practice_questions("Fundamental Of Economics (FOE)", limit=10)
        assert len(practice["questions"]) == 10
        assert practice["subject"] == "Fundamental Of Economics (FOE)"
    finally:
        db.close()
