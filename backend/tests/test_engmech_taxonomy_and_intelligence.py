"""
Comprehensive test suite for Course 21: Engineering Mechanics (ENGMECH).
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
from backend.services.taxonomy_rules.engmech_rules import ENGMECH_TAXONOMY_RULES
from scripts.curriculum.map_engmech_questions_to_topics import run_engmech_mapping


@pytest.fixture
def client():
    return TestClient(app)


def test_engmech_registry_integrity():
    """Verify Course 21 declarative structure and invariants in taxonomy registry."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    assert registry.has_course(21), "Course 21 must be registered in taxonomy registry"
    entry = registry.get_course(21)

    assert entry.course.id == 21
    assert entry.course.canonical_code == "21MEB101T"
    assert entry.course.code == "SEM2-ENGMECH"
    assert entry.course.name == "Engineering Mechanics"
    assert entry.provenance.regulation == "2021"

    # Exactly 5 units
    assert len(entry.units) == 5
    assert [u.number for u in entry.units] == [1, 2, 3, 4, 5]

    # Exactly 25 topics
    total_topics = sum(len(u.topics) for u in entry.units)
    assert total_topics == 25

    # Check topic rules count and topic ID range 389..413
    rules = registry.get_topic_rules(21)
    assert len(rules) == 25
    topic_ids = [r.topic_id for r in rules]
    assert sorted(topic_ids) == list(range(389, 414))


def test_engmech_database_validation():
    """Verify declarative definition matches current SQLite database taxonomy for Course 21."""
    registry = get_taxonomy_registry()
    db = SessionLocal()
    try:
        val = registry.validate_against_database(21, db)
        assert val["valid"] is True, f"DB validation failed: {val.get('mismatches')}"
        assert val["units_verified"] == 5
        assert val["topics_verified"] == 25
        assert len(val["mismatches"]) == 0
    finally:
        db.close()


def test_engmech_no_cross_course_leakage():
    """Verify zero overlap in topic IDs and unit IDs between Course 21 and other courses."""
    registry = get_taxonomy_registry()
    chem = registry.get_course(2)
    spcm = registry.get_course(13)
    eee = registry.get_course(14)
    acca = registry.get_course(16)
    oodp = registry.get_course(17)
    espcb = registry.get_course(18)
    engmech = registry.get_course(21)

    em_topic_ids = {t.id for u in engmech.units for t in u.topics}
    for other in [chem, spcm, eee, acca, oodp, espcb]:
        other_tids = {t.id for u in other.units for t in u.topics}
        assert em_topic_ids.isdisjoint(other_tids), f"ENGMECH topic IDs must not overlap with {other.course.name}"

    em_unit_ids = {u.id for u in engmech.units}
    for other in [chem, spcm, eee, acca, oodp, espcb]:
        other_uids = {u.id for u in other.units}
        assert em_unit_ids.isdisjoint(other_uids), f"ENGMECH unit IDs must not overlap with {other.course.name}"


def test_engmech_classifier_behavior_across_all_units():
    """Verify classifier correctly matches domain prompts across all 5 units with high confidence."""
    classifier = TaxonomyClassifierService(ENGMECH_TAXONOMY_RULES)

    # Unit 1: Moments and Varignon's Theorem
    prop1 = classifier.classify(1, "State and prove Varignon's theorem of moments with a neat sketch.")
    assert prop1.confidence == "HIGH"
    assert prop1.topic_id == 391

    # Unit 2: Laws of Dry Friction
    prop2 = classifier.classify(2, "Explain the laws of dry friction and define limiting friction.")
    assert prop2.confidence == "HIGH"
    assert prop2.topic_id == 394

    # Unit 3: Centroid
    prop3 = classifier.classify(3, "Locate the centroid of plane area shown in figure.")
    assert prop3.confidence == "HIGH"
    assert prop3.topic_id == 399

    # Unit 4: Rectilinear Motion
    prop4 = classifier.classify(4, "Explain rectilinear motion of particles and find position velocity and acceleration.")
    assert prop4.confidence == "HIGH"
    assert prop4.topic_id == 404

    # Unit 5: General Plane Motion
    prop5 = classifier.classify(5, "Explain general plane motion and instantaneous centre of rotation of a rigid body.")
    assert prop5.confidence == "HIGH"
    assert prop5.topic_id == 410


def test_engmech_ambiguity_and_guardrail_rejections():
    """Verify conservative matching flags conflicting topics as AMBIGUOUS and ignores unmapped prompts."""
    classifier = TaxonomyClassifierService(ENGMECH_TAXONOMY_RULES)

    # Question spanning both Free Body Diagrams and Support Reactions
    composite_text = "Draw free body diagram for equilibrium of particles and find the reactions at support."
    prop_amb = classifier.classify(10, composite_text)
    assert prop_amb.confidence == "AMBIGUOUS"
    assert prop_amb.topic_id is None
    assert len(prop_amb.candidate_topics) >= 2

    # Generic prompt
    prop_un = classifier.classify(11, "Candidates must verify the question paper code before writing.")
    assert prop_un.confidence == "UNMAPPED"
    assert prop_un.topic_id is None


def test_engmech_mapping_persistence_and_idempotency():
    """Verify that mapped questions exist in question_topic and rerun produces 0 insertions."""
    db = SessionLocal()
    try:
        # Check mapped count in DB
        mapped_count = (
            db.query(question_topic)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 21)
            .count()
        )
        assert mapped_count >= 55, f"Expected at least 55 mapped questions, got {mapped_count}"

        # Verify all mapped topics belong to Course 21 (IDs 389..413)
        topic_ids = [
            r[1] for r in
            db.query(question_topic.c.question_id, question_topic.c.topic_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 21)
            .all()
        ]
        assert all(389 <= tid <= 413 for tid in topic_ids), "Mapped topics must be in range 389..413"

        # Rerun dry-run: 0 new insertions, 0 conflicts
        res = run_engmech_mapping(apply_changes=False)
        assert res["new_insertions"] == 0
        assert res["conflicts"] == 0
        assert res["already_mapped"] >= 55
    finally:
        db.close()


def test_engmech_intelligence_snapshot_reports_topic_mode(client: TestClient):
    """Verify Course 21 intelligence snapshot transitions to topic mode with calibrated predictions."""
    res = client.get("/api/intelligence/21")
    assert res.status_code == 200
    data = res.json()

    assert data["course"]["id"] == 21
    assert data["course"]["code"] == "SEM2-ENGMECH"
    assert data["course"]["canonical_code"] == "21MEB101T"
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 25
    assert data["prediction_mode"] == "topic"

    predictions = data.get("predictions", [])
    assert len(predictions) > 0, "Topic predictions must be generated"
    for p in predictions:
        assert p["category"] == "topic"
        assert p["topic_id"] is not None
        assert 389 <= p["topic_id"] <= 413
        assert p["prediction_score"] >= 0.0
        assert p["confidence"] in ("HIGH", "MEDIUM", "LOW")


def test_engmech_study_priorities_endpoint(client: TestClient):
    """Verify study priorities endpoint supports all Course 21 identifiers and returns topic plan."""
    for ident in ["21", "SEM2-ENGMECH", "21MEB101T", "Engineering Mechanics"]:
        res = client.get(f"/api/study/priorities/{ident}")
        assert res.status_code == 200, f"Failed for identifier: {ident}"
        data = res.json()
        assert data["plan_mode"] == "topic"
        assert data["has_topic_taxonomy"] is True
        assert len(data["priorities"]) > 0


def test_engmech_practice_endpoint(client: TestClient):
    """Verify practice questions endpoint returns valid questions for Course 21."""
    res = client.get("/api/practice/21?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("questions", [])) == 10
