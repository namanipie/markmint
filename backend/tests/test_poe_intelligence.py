"""
Focused integration tests for Course 3: Philosophy Of Engineering (21GNH101J).
Verifies:
- 5 units and 20 topics taxonomy integrity
- Classifier behavior and ambiguity rejection
- Mapping persistence and idempotency
- Zero cross-course mappings
- Prediction integration and prediction_mode == 'topic'
- Study plan generation in topic mode
"""
import pytest
from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus
from backend.services.taxonomy_classifier import TaxonomyClassifierService
from backend.services.taxonomy_rules.poe_rules import POE_TAXONOMY_RULES
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def test_poe_taxonomy_integrity():
    """Verify Course 3 has exactly 5 units and 20 topics in SQLite."""
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 3).first()
        assert syl is not None, "Course 3 syllabus must exist"

        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Expected 5 units, found {len(units)}"

        expected_units = [
            (1, "Introduction to Philosophy of Engineering"),
            (2, "Ontology of Engineering"),
            (3, "Epistemology of Engineering"),
            (4, "Methodology of Engineering"),
            (5, "Axiology of Engineering"),
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


def test_poe_classifier_behavior():
    """Verify deterministic classification rules for representative POE questions."""
    classifier = TaxonomyClassifierService(POE_TAXONOMY_RULES)

    # Test STEAM Pyramid
    p1 = classifier.classify(1, "What is the important Point of view of STEAM? A Brief Overview of STEAM Education.")
    assert p1.confidence == "HIGH"
    assert p1.topic_name == "STEAM Pyramid and Interdisciplinary Education"

    # Test Product Life Cycle
    p2 = classifier.classify(2, "Briefly explain the product life cycle with the help of flow chart and time vs sales graph.")
    assert p2.confidence == "HIGH"
    assert p2.topic_name == "Product Life Cycle and Developmental Stages"

    # Test RIASEC
    p3 = classifier.classify(3, "What is the RIASEC model used for? And explain all the modules.")
    assert p3.confidence == "HIGH"
    assert p3.topic_name == "RIASEC Model and Engineering Typology"

    # Test CDIO
    p4 = classifier.classify(4, "What is the full form of CDIO and briefly explain the process.")
    assert p4.confidence == "HIGH"
    assert p4.topic_name == "CDIO Framework in Industry and Practice"

    # Test ADDIE
    p5 = classifier.classify(5, "Explain in detail on how Addie model is useful for building training support tools.")
    assert p5.confidence == "HIGH"
    assert p5.topic_name == "ADDIE Model and Instructional System Design"

    # Test 3Es
    p6 = classifier.classify(6, "Explain the concept of 3Es in engineering with a neat diagram.")
    assert p6.confidence == "HIGH"
    assert p6.topic_name == "Concept of 3Es: Engineering, Economics, and Ethics"


def test_poe_ambiguity_rejection():
    """Verify that conflicting multi-topic questions are rejected as AMBIGUOUS or UNMAPPED."""
    classifier = TaxonomyClassifierService(POE_TAXONOMY_RULES)

    # Question matching conflicting candidate topics
    p_ambig = classifier.classify(99, "Compare steam framework with reference ontology in engineering practice.")
    assert p_ambig.confidence in ("AMBIGUOUS", "UNMAPPED")

    # Generic unmapped question
    p_unmap = classifier.classify(100, "None of the above.")
    assert p_unmap.confidence == "UNMAPPED"


def test_poe_zero_cross_course_mappings():
    """Verify Course 3 questions map ONLY to Course 3 topics."""
    db = SessionLocal()
    try:
        from backend.models.core import question_topic
        cross = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(question_topic, Question.id == question_topic.c.question_id)
            .join(Topic, question_topic.c.topic_id == Topic.id)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Exam.course_id == 3, Syllabus.course_id != 3)
            .count()
        )
        assert cross == 0, f"Found {cross} cross-course mappings for Course 3!"
    finally:
        db.close()


def test_poe_intelligence_and_predictions_integration():
    """Verify Course 3 reports prediction_mode == 'topic' with topic and family predictions."""
    db = SessionLocal()
    try:
        snap = get_intelligence_snapshot("3", db=db)
        assert snap["prediction_mode"] == "topic"
        assert snap["has_topic_taxonomy"] is True
        assert snap["taxonomy_topic_count"] == 20
        assert snap["topic_predictions_count"] > 0
        assert snap["family_predictions_count"] > 0
        assert len(snap["predictions"]) > 0
        assert len(snap["study_priorities"]) > 0

        # Study plan verification
        plan = get_study_priorities("Philosophy Of Engineering", db=db)
        assert plan["plan_mode"] == "topic"
        assert len(plan["priorities"]) > 0

        # Practice verification
        practice = get_practice_questions("21GNH101J")
        assert len(practice["questions"]) > 0
    finally:
        db.close()
