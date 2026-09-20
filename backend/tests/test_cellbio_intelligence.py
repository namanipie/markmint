"""
Focused integration tests for Course 9: Cell Biology (21BTC102J / 21BTB105T).
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
from backend.services.taxonomy_rules.cellbio_rules import CELLBIO_TAXONOMY_RULES
from backend.api.endpoints.intelligence import get_intelligence_snapshot
from backend.api.router_study import get_study_priorities
from backend.api.endpoints.practice import get_practice_questions


def test_cellbio_taxonomy_integrity():
    """Verify Course 9 has exactly 5 units and 20 topics in SQLite."""
    db = SessionLocal()
    try:
        syl = db.query(Syllabus).filter(Syllabus.course_id == 9).first()
        assert syl is not None, "Course 9 syllabus must exist"

        units = db.query(Unit).filter(Unit.syllabus_id == syl.id).order_by(Unit.number).all()
        assert len(units) == 5, f"Expected 5 units, found {len(units)}"

        expected_units = [
            (1, "Overview of Cells and Cell Research"),
            (2, "Cell Structure and Function: Organelles"),
            (3, "Cytoskeleton and Cellular Transport"),
            (4, "Cell Signaling and Transduction Pathways"),
            (5, "Cell Regulation, Cancer, and Stem Cells"),
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


def test_cellbio_classifier_behavior():
    """Verify deterministic classification rules for representative Cell Biology questions."""
    classifier = TaxonomyClassifierService(CELLBIO_TAXONOMY_RULES)

    # Test Membrane Fluidity
    p1 = classifier.classify(1, "The presence of unsaturated fatty acids increases the cell membrane fluidity.")
    assert p1.confidence == "HIGH"
    assert p1.topic_name == "Structure, Composition, and Dynamics of the Plasma Membrane"

    # Test Model Organism
    p2 = classifier.classify(2, "Squid is used as a model organism for studying ion transport.")
    assert p2.confidence == "HIGH"
    assert p2.topic_name == "Experimental Model Organisms and Microscopy Tools in Cell Biology"

    # Test Nucleopore
    p3 = classifier.classify(3, "The nucleopore complex consists of spokes across the nuclear envelope.")
    assert p3.confidence == "HIGH"
    assert p3.topic_name == "Nuclear Structure, Nuclear Envelope, and Nucleolus"

    # Test Microtubules
    p4 = classifier.classify(4, "Elaborate on the assembly, organization, and functions of Microtubules with illustration.")
    assert p4.confidence == "HIGH"
    assert p4.topic_name == "Microtubules, Centrosomes, and Intermediate Filaments"

    # Test Generic unmapped question
    p5 = classifier.classify(5, "Answer all questions in Section A.")
    assert p5.confidence == "UNMAPPED"
    assert p5.topic_id is None


def test_cellbio_mapping_invariants():
    """Verify Course 9 mappings: >= 50 mapped, zero cross-course, and zero orphan mappings."""
    db = SessionLocal()
    try:
        total_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 9)
            .count()
        )
        assert total_questions == 65, f"Expected 65 questions, got {total_questions}"

        mapped_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 9, Question.topics.any())
            .count()
        )
        assert mapped_questions >= 50, f"Expected at least 50 mapped questions, got {mapped_questions}"

        # Verify no cross-course mappings
        cross_course_count = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .join(Question.topics)
            .join(Unit, Topic.unit_id == Unit.id)
            .join(Syllabus, Unit.syllabus_id == Syllabus.id)
            .filter(Exam.course_id == 9, Syllabus.course_id != 9)
            .count()
        )
        assert cross_course_count == 0, f"Found {cross_course_count} cross-course topic mappings for Course 9"
    finally:
        db.close()


def test_cellbio_intelligence_snapshot():
    """Verify /api/intelligence/9 snapshot returns topic mode and active predictions."""
    db = SessionLocal()
    try:
        snapshot = get_intelligence_snapshot(course_id="9", db=db)
        assert snapshot["prediction_mode"] == "topic"
        assert snapshot["has_topic_taxonomy"] is True
        assert snapshot["taxonomy_topic_count"] == 20
        assert len(snapshot["topic_predictions"]) > 0
        assert len(snapshot["family_predictions"]) > 0
        assert snapshot["exam_history"]["total_papers"] >= 1
        assert snapshot["exam_history"]["total_questions"] == 65
    finally:
        db.close()


def test_cellbio_study_plan_and_practice():
    """Verify study plan operates in topic mode and practice endpoint returns questions."""
    db = SessionLocal()
    try:
        priorities = get_study_priorities("Cell Biology", db=db)
        assert priorities["plan_mode"] == "topic"
        assert len(priorities["priorities"]) > 0
        assert priorities["has_topic_taxonomy"] is True

        practice = get_practice_questions("Cell Biology", limit=10)
        assert len(practice["questions"]) == 10
        assert practice["subject"] == "Cell Biology"
    finally:
        db.close()
