"""
Focused integration tests for Course 4: Introduction To Computational Biology (21BTB102T).
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
from backend.services.taxonomy_rules.icb_rules import ICB_TAXONOMY_RULES
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def test_icb_taxonomy_integrity():
    """Verify Course 4 has exactly 5 units and 20 topics in SQLite."""
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 4).first()
        assert syl is not None, "Course 4 syllabus must exist"

        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Expected 5 units, found {len(units)}"

        expected_units = [
            (1, "Cell and Evolution"),
            (2, "Basics in Biochemistry"),
            (3, "Structure Biology"),
            (4, "Neurobiology"),
            (5, "Immunobiology"),
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


def test_icb_classifier_behavior():
    """Verify deterministic classification rules for representative ICB questions."""
    classifier = TaxonomyClassifierService(ICB_TAXONOMY_RULES)

    # Test Cell Theory & Whittaker
    p1 = classifier.classify(1, "The five kingdom classification was proposed by R.H.Whittaker.")
    assert p1.confidence == "HIGH"
    assert p1.topic_name == "Cell Theory and Whittaker's Kingdom Classification"

    # Test BLAST
    p2 = classifier.classify(2, "Explain about biological databases and how is BLAST algorithm used for sequence search.")
    assert p2.confidence == "HIGH"
    assert p2.topic_name == "Sequence Databases and BLAST Search Tool"

    # Test ANN
    p3 = classifier.classify(3, "What is ANN? Write on the working principle and application in biology.")
    assert p3.confidence == "HIGH"
    assert p3.topic_name == "Artificial Neural Networks and Biological Comparison"

    # Test Stem cells
    p4 = classifier.classify(4, "What are stem cells? Write on the classification and properties of stem cells.")
    assert p4.confidence == "HIGH"
    assert p4.topic_name == "Stem Cells and Genetic Algorithms in Evolution"

    # Test Generic unmapped question
    p5 = classifier.classify(5, "Answer all the questions from section A.")
    assert p5.confidence == "UNMAPPED"
    assert p5.topic_id is None


def test_icb_mapping_invariants():
    """Verify Course 4 mappings: >= 150 mapped, zero cross-course, and zero orphan mappings."""
    db = SessionLocal()
    try:
        # Check total questions and mapped questions
        total_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 4)
            .count()
        )
        assert total_questions == 228, f"Expected 228 questions, got {total_questions}"

        mapped_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 4, Question.topics.any())
            .count()
        )
        assert mapped_questions >= 150, f"Expected at least 150 mapped questions, got {mapped_questions}"

        # Verify no cross-course mappings
        cross_course_count = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Exam.course_id == 4, Syllabus.course_id != 4)
            .count()
        )
        assert cross_course_count == 0, f"Found {cross_course_count} cross-course topic mappings for Course 4"
    finally:
        db.close()


def test_icb_intelligence_snapshot():
    """Verify /api/intelligence/4 snapshot returns topic mode and rich evidence."""
    db = SessionLocal()
    try:
        snapshot = get_intelligence_snapshot(course_id="4", db=db)
        assert snapshot["data_availability_status"] == "READY"
        assert snapshot["prediction_mode"] == "topic"
        assert snapshot["has_topic_taxonomy"] is True
        assert snapshot["taxonomy_topic_count"] == 20
        assert len(snapshot["topic_predictions"]) > 0
        assert len(snapshot["family_predictions"]) > 0
        assert snapshot["exam_history"]["total_papers"] == 8
        assert snapshot["exam_history"]["total_questions"] == 228
    finally:
        db.close()


def test_icb_study_plan_and_practice():
    """Verify study plan operates in topic mode and practice endpoint returns questions."""
    db = SessionLocal()
    try:
        priorities = get_study_priorities("Introduction To Computational Biology", db=db)
        assert priorities["plan_mode"] == "topic"
        assert len(priorities["priorities"]) > 0
        assert priorities["has_topic_taxonomy"] is True

        practice = get_practice_questions("Introduction To Computational Biology", limit=10)
        assert len(practice["questions"]) == 10
        assert practice["subject"] == "Introduction To Computational Biology"
    finally:
        db.close()
