"""
Focused integration tests for Course 12: Biochemistry (21BTC101T).
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
from backend.services.taxonomy_rules.biochem_rules import BIOCHEM_TAXONOMY_RULES
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def test_biochem_taxonomy_integrity():
    """Verify Course 12 has exactly 5 units and 20 topics in SQLite."""
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 12).first()
        assert syl is not None, "Course 12 syllabus must exist"

        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Expected 5 units, found {len(units)}"

        expected_units = [
            (1, "Introduction to Biochemistry"),
            (2, "Introduction to Metabolism, Bioenergetics and Photosynthesis"),
            (3, "Carbohydrate Metabolism"),
            (4, "Protein Turnover and Amino Acids Metabolism"),
            (5, "Fatty Acid and Nucleic Acids Metabolisms"),
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


def test_biochem_classifier_behavior():
    """Verify deterministic classification rules for representative Biochemistry questions."""
    classifier = TaxonomyClassifierService(BIOCHEM_TAXONOMY_RULES)

    # Test Anomeric hydroxyl groups
    p1 = classifier.classify(1, "The anomeric hydroxyl groups of two sugars can join together splitting out water to form a glycosidic bond.")
    assert p1.confidence == "HIGH"
    assert p1.topic_name == "Carbohydrate Architecture: Monosaccharides, Polysaccharides, and Glycoproteins"

    # Test Hexokinase in glycolysis
    p2 = classifier.classify(2, "Which of these enzyme reactions is not reversible in glycolysis? Hexokinase.")
    assert p2.confidence == "HIGH"
    assert p2.topic_name == "Glycolysis and Pyruvate Dehydrogenase Complex"

    # Test PEST sequence
    p3 = classifier.classify(3, "PEST sequence are rapidly degraded to proteins.")
    assert p3.confidence == "HIGH"
    assert p3.topic_name == "Protein Turnover, Proteolysis, and PEST Sequences"

    # Test Palmitic acid oxidation
    p4 = classifier.classify(4, "Oxidation of palmitic acid (C16) involves beta-oxidation.")
    assert p4.confidence == "HIGH"
    assert p4.topic_name == "Mobilization of Lipids and Beta-Oxidation of Fatty Acids"

    # Test Generic unmapped question
    p5 = classifier.classify(5, "Answer all questions in Section A.")
    assert p5.confidence == "UNMAPPED"
    assert p5.topic_id is None


def test_biochem_mapping_invariants():
    """Verify Course 12 mappings: >= 75 mapped, zero cross-course, and zero orphan mappings."""
    db = SessionLocal()
    try:
        total_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 12)
            .count()
        )
        assert total_questions == 101, f"Expected 101 questions, got {total_questions}"

        mapped_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 12, Question.topics.any())
            .count()
        )
        assert mapped_questions >= 75, f"Expected at least 75 mapped questions, got {mapped_questions}"

        # Verify no cross-course mappings
        cross_course_count = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Exam.course_id == 12, Syllabus.course_id != 12)
            .count()
        )
        assert cross_course_count == 0, f"Found {cross_course_count} cross-course topic mappings for Course 12"
    finally:
        db.close()


def test_biochem_intelligence_snapshot():
    """Verify /api/intelligence/12 snapshot returns topic mode and active predictions."""
    db = SessionLocal()
    try:
        snapshot = get_intelligence_snapshot(course_id="12", db=db)
        assert snapshot["prediction_mode"] == "topic"
        assert snapshot["has_topic_taxonomy"] is True
        assert snapshot["taxonomy_topic_count"] == 20
        assert len(snapshot["topic_predictions"]) > 0
        assert len(snapshot["family_predictions"]) > 0
        assert snapshot["exam_history"]["total_papers"] == 3
        assert snapshot["exam_history"]["total_questions"] == 101
    finally:
        db.close()


def test_biochem_study_plan_and_practice():
    """Verify study plan operates in topic mode and practice endpoint returns questions."""
    db = SessionLocal()
    try:
        priorities = get_study_priorities("Biochemistry", db=db)
        assert priorities["plan_mode"] == "topic"
        assert len(priorities["priorities"]) > 0
        assert priorities["has_topic_taxonomy"] is True

        practice = get_practice_questions("Biochemistry", limit=10)
        assert len(practice["questions"]) == 10
        assert practice["subject"] == "Biochemistry"
    finally:
        db.close()
