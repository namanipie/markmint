"""
Comprehensive test suite for Course 17: Object Oriented Design and Programming (OODP).
Validates:
1. Declarative taxonomy registry integrity and database consistency.
2. Conservative deterministic classifier behavior across all 5 units.
3. Ambiguity handling and negative guardrail rejection.
4. Mapping persistence, scope enforcement, and idempotent rerun.
5. Zero cross-course leakage.
6. Topic-mode intelligence snapshot, predictions, study plan, and practice endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.database import SessionLocal
from backend.models.core import Question, Section, Exam, question_topic
from backend.services.taxonomy_registry import get_taxonomy_registry, reset_taxonomy_registry
from backend.services.taxonomy_classifier import TaxonomyClassifierService
from backend.services.taxonomy_rules.oodp_rules import OODP_TAXONOMY_RULES
from scripts.curriculum.map_oodp_questions_to_topics import run_oodp_mapping


@pytest.fixture
def client():
    return TestClient(app)


def test_oodp_registry_integrity():
    """Verify Course 17 declarative structure and invariants in taxonomy registry."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    assert registry.has_course(17), "Course 17 must be registered in taxonomy registry"
    entry = registry.get_course(17)

    assert entry.course.id == 17
    assert entry.course.canonical_code == "21CSC102J"
    assert entry.course.code == "SEM2-OODP"
    assert entry.course.name == "Object Oriented Design and Programming"
    assert entry.provenance.regulation == "2021"

    # Exactly 5 units
    assert len(entry.units) == 5
    assert [u.number for u in entry.units] == [1, 2, 3, 4, 5]

    # Exactly 25 topics
    total_topics = sum(len(u.topics) for u in entry.units)
    assert total_topics == 25

    # Check topic rules count and topic ID range 339..363
    rules = registry.get_topic_rules(17)
    assert len(rules) == 25
    topic_ids = [r.topic_id for r in rules]
    assert sorted(topic_ids) == list(range(339, 364))


def test_oodp_database_validation():
    """Verify declarative definition matches current SQLite database taxonomy for Course 17."""
    registry = get_taxonomy_registry()
    db = SessionLocal()
    try:
        val = registry.validate_against_database(17, db)
        assert val["valid"] is True, f"DB validation failed: {val.get('mismatches')}"
        assert val["units_verified"] == 5
        assert val["topics_verified"] == 25
        assert len(val["mismatches"]) == 0
    finally:
        db.close()


def test_oodp_no_cross_course_leakage():
    """Verify zero overlap in topic IDs and unit IDs between Course 17 and other courses (2, 13, 14, 16)."""
    registry = get_taxonomy_registry()
    chem = registry.get_course(2)
    spcm = registry.get_course(13)
    eee = registry.get_course(14)
    acca = registry.get_course(16)
    oodp = registry.get_course(17)

    oodp_topic_ids = {t.id for u in oodp.units for t in u.topics}
    chem_topic_ids = {t.id for u in chem.units for t in u.topics}
    spcm_topic_ids = {t.id for u in spcm.units for t in u.topics}
    eee_topic_ids = {t.id for u in eee.units for t in u.topics}
    acca_topic_ids = {t.id for u in acca.units for t in u.topics}

    assert oodp_topic_ids.isdisjoint(chem_topic_ids), "OODP topic IDs must not overlap with Chemistry"
    assert oodp_topic_ids.isdisjoint(spcm_topic_ids), "OODP topic IDs must not overlap with SPCM"
    assert oodp_topic_ids.isdisjoint(eee_topic_ids), "OODP topic IDs must not overlap with EEE"
    assert oodp_topic_ids.isdisjoint(acca_topic_ids), "OODP topic IDs must not overlap with ACCA"

    oodp_unit_ids = {u.id for u in oodp.units}
    chem_unit_ids = {u.id for u in chem.units}
    spcm_unit_ids = {u.id for u in spcm.units}
    eee_unit_ids = {u.id for u in eee.units}
    acca_unit_ids = {u.id for u in acca.units}

    assert oodp_unit_ids.isdisjoint(chem_unit_ids), "OODP unit IDs must not overlap with Chemistry"
    assert oodp_unit_ids.isdisjoint(spcm_unit_ids), "OODP unit IDs must not overlap with SPCM"
    assert oodp_unit_ids.isdisjoint(eee_unit_ids), "OODP unit IDs must not overlap with EEE"
    assert oodp_unit_ids.isdisjoint(acca_unit_ids), "OODP unit IDs must not overlap with ACCA"


def test_oodp_classifier_behavior_across_all_units():
    """Verify classifier correctly matches domain prompts across all 5 units with high confidence."""
    classifier = TaxonomyClassifierService(OODP_TAXONOMY_RULES)

    # Unit 1: UML Class Diagrams and Class Relationships
    prop1 = classifier.classify(1, "Draw a UML class diagram showing aggregation and composition relationships.")
    assert prop1.confidence == "HIGH"
    assert prop1.topic_id == 342

    # Unit 2: Types of Constructors
    prop2 = classifier.classify(2, "Explain the working of copy constructor and how it takes an object as argument.")
    assert prop2.confidence == "HIGH"
    assert prop2.topic_id == 345

    # Unit 3: Virtual Functions, Dynamic Binding, and Abstract Classes
    prop3 = classifier.classify(3, "Demonstrate runtime polymorphism using pure virtual function and abstract class.")
    assert prop3.confidence == "HIGH"
    assert prop3.topic_id == 352

    # Unit 4: Generic Programming and Function Templates
    prop4 = classifier.classify(4, "Explain the syntax for template function with an illustrative example.")
    assert prop4.confidence == "HIGH"
    assert prop4.topic_id == 354

    # Unit 5: STL Sequence Containers
    prop5 = classifier.classify(5, "Write a C++ program to demonstrate sequence container vector and its push_back method.")
    assert prop5.confidence == "HIGH"
    assert prop5.topic_id == 360


def test_oodp_ambiguity_and_guardrail_rejections():
    """Verify conservative matching flags conflicting topics as AMBIGUOUS and ignores unmapped prompts."""
    classifier = TaxonomyClassifierService(OODP_TAXONOMY_RULES)

    # Multi-part question with two distinct strong topics
    composite_text = "Explain the copy constructor in C++ --- OR --- Draw a sequence diagram with lifeline and messages"
    prop_amb = classifier.classify(10, composite_text)
    assert prop_amb.confidence == "AMBIGUOUS"
    assert prop_amb.topic_id is None
    assert len(prop_amb.candidate_topics) >= 2

    # Generic prompt
    prop_un = classifier.classify(11, "All candidates must write down their registration number on page 1.")
    assert prop_un.confidence == "UNMAPPED"
    assert prop_un.topic_id is None


def test_oodp_mapping_persistence_and_idempotency():
    """Verify that mapped questions exist in question_topic and rerun produces 0 insertions."""
    db = SessionLocal()
    try:
        # Check mapped count in DB
        mapped_count = (
            db.query(question_topic)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 17)
            .count()
        )
        assert mapped_count >= 160, f"Expected at least 160 mapped questions, got {mapped_count}"

        # Verify all mapped topics belong to Course 17 (IDs 339..363)
        topic_ids = [
            r[1] for r in
            db.query(question_topic.c.question_id, question_topic.c.topic_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 17)
            .all()
        ]
        assert all(339 <= tid <= 363 for tid in topic_ids), "Mapped topics must be in range 339..363"

        # Rerun dry-run: 0 new insertions, 0 conflicts
        res = run_oodp_mapping(apply_changes=False)
        assert res["new_insertions"] == 0
        assert res["conflicts"] == 0
        assert res["already_mapped"] >= 160
    finally:
        db.close()


def test_oodp_intelligence_snapshot_reports_topic_mode(client: TestClient):
    """Verify Course 17 intelligence snapshot transitions to topic mode with calibrated predictions."""
    res = client.get("/api/intelligence/17")
    assert res.status_code == 200
    data = res.json()

    assert data["course"]["id"] == 17
    assert data["course"]["code"] == "SEM2-OODP"
    assert data["course"]["canonical_code"] == "21CSC102J"
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 25
    assert data["prediction_mode"] == "topic"

    predictions = data.get("predictions", [])
    assert len(predictions) > 0, "Topic predictions must be generated"
    for p in predictions:
        assert p["category"] == "topic"
        assert p["topic_id"] is not None
        assert 339 <= p["topic_id"] <= 363
        assert p["prediction_score"] >= 0.0
        assert p["confidence"] in ("HIGH", "MEDIUM", "LOW")


def test_oodp_study_priorities_endpoint(client: TestClient):
    """Verify study priorities endpoint supports all Course 17 identifiers and returns topic plan."""
    for ident in ["17", "SEM2-OODP", "21CSC102J", "Object Oriented Design and Programming"]:
        res = client.get(f"/api/study/priorities/{ident}")
        assert res.status_code == 200, f"Failed for identifier: {ident}"
        data = res.json()
        assert data["plan_mode"] == "topic"
        assert data["has_topic_taxonomy"] is True
        assert len(data["priorities"]) > 0


def test_oodp_practice_endpoint(client: TestClient):
    """Verify practice questions endpoint returns valid questions for Course 17."""
    res = client.get("/api/practice/17?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("questions", [])) == 10
