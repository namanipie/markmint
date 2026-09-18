"""
Comprehensive test suite for Course 16: Advanced Calculus and Complex Analysis (ACCA).
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
from backend.services.taxonomy_rules.acca_rules import ACCA_TAXONOMY_RULES
from scripts.curriculum.map_acca_questions_to_topics import run_acca_mapping


@pytest.fixture
def client():
    return TestClient(app)


def test_acca_registry_integrity():
    """Verify Course 16 declarative structure and invariants in taxonomy registry."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    assert registry.has_course(16), "Course 16 must be registered in taxonomy registry"
    entry = registry.get_course(16)

    assert entry.course.id == 16
    assert entry.course.canonical_code == "21MAB102T"
    assert entry.course.code == "SEM2-ACCA"
    assert entry.course.name == "Advanced Calculus and Complex Analysis"
    assert entry.provenance.regulation == "2021"

    # Exactly 5 units
    assert len(entry.units) == 5
    assert [u.number for u in entry.units] == [1, 2, 3, 4, 5]

    # Exactly 24 topics
    total_topics = sum(len(u.topics) for u in entry.units)
    assert total_topics == 24

    # Check topic rules count and topic ID range 315..338
    rules = registry.get_topic_rules(16)
    assert len(rules) == 24
    topic_ids = [r.topic_id for r in rules]
    assert sorted(topic_ids) == list(range(315, 339))


def test_acca_database_validation():
    """Verify declarative definition matches current SQLite database taxonomy for Course 16."""
    registry = get_taxonomy_registry()
    db = SessionLocal()
    try:
        val = registry.validate_against_database(16, db)
        assert val["valid"] is True, f"DB validation failed: {val.get('mismatches')}"
        assert val["units_verified"] == 5
        assert val["topics_verified"] == 24
        assert len(val["mismatches"]) == 0
    finally:
        db.close()


def test_acca_no_cross_course_leakage():
    """Verify zero overlap in topic IDs and unit IDs between Course 16 and other courses (2, 13, 14)."""
    registry = get_taxonomy_registry()
    chem = registry.get_course(2)
    spcm = registry.get_course(13)
    eee = registry.get_course(14)
    acca = registry.get_course(16)

    acca_topic_ids = {t.id for u in acca.units for t in u.topics}
    chem_topic_ids = {t.id for u in chem.units for t in u.topics}
    spcm_topic_ids = {t.id for u in spcm.units for t in u.topics}
    eee_topic_ids = {t.id for u in eee.units for t in u.topics}

    assert acca_topic_ids.isdisjoint(chem_topic_ids), "ACCA topic IDs must not overlap with Chemistry"
    assert acca_topic_ids.isdisjoint(spcm_topic_ids), "ACCA topic IDs must not overlap with SPCM"
    assert acca_topic_ids.isdisjoint(eee_topic_ids), "ACCA topic IDs must not overlap with EEE"

    acca_unit_ids = {u.id for u in acca.units}
    chem_unit_ids = {u.id for u in chem.units}
    spcm_unit_ids = {u.id for u in spcm.units}
    eee_unit_ids = {u.id for u in eee.units}

    assert acca_unit_ids.isdisjoint(chem_unit_ids), "ACCA unit IDs must not overlap with Chemistry"
    assert acca_unit_ids.isdisjoint(spcm_unit_ids), "ACCA unit IDs must not overlap with SPCM"
    assert acca_unit_ids.isdisjoint(eee_unit_ids), "ACCA unit IDs must not overlap with EEE"


def test_acca_classifier_behavior_across_all_units():
    """Verify classifier correctly matches domain prompts across all 5 units with high confidence."""
    classifier = TaxonomyClassifierService(ACCA_TAXONOMY_RULES)

    # Unit 1: Multiple Integrals - Change of Order of Integration
    prop1 = classifier.classify(1, "Change the order of integration and evaluate the double integral.")
    assert prop1.confidence == "HIGH"
    assert prop1.topic_id == 316

    # Unit 2: Vector Calculus - Green's Theorem
    prop2 = classifier.classify(2, "Verify Green's theorem in a plane for the vector field around the closed curve.")
    assert prop2.confidence == "HIGH"
    assert prop2.topic_id == 321

    # Unit 3: Laplace Transforms - Convolution Theorem
    prop3 = classifier.classify(3, "Using convolution theorem, find the inverse Laplace transform of the given function.")
    assert prop3.confidence == "HIGH"
    assert prop3.topic_id == 327

    # Unit 4: Analytic Functions - Cauchy-Riemann Equations
    prop4 = classifier.classify(4, "Prove that the analytic function satisfies Cauchy-Riemann equations in polar form.")
    assert prop4.confidence == "HIGH"
    assert prop4.topic_id == 329

    # Unit 5: Complex Integration - Residue Theorem
    prop5 = classifier.classify(5, "Evaluate the contour integral around the circle using Cauchy's residue theorem.")
    assert prop5.confidence == "HIGH"
    assert prop5.topic_id == 337


def test_acca_ambiguity_and_guardrail_rejections():
    """Verify conservative matching flags conflicting topics as AMBIGUOUS and ignores unmapped prompts."""
    classifier = TaxonomyClassifierService(ACCA_TAXONOMY_RULES)

    # Question with both Laplace transform (Topic 324) and inverse transform L^-1 (Topic 326)
    composite_text = "Find the laplace transform of f(t) = 1 --- OR --- Find L^-1 [ log(s/(s+1)) ]"
    prop_amb = classifier.classify(10, composite_text)
    assert prop_amb.confidence == "AMBIGUOUS"
    assert prop_amb.topic_id is None
    assert len(prop_amb.candidate_topics) >= 2

    # Generic prompt
    prop_un = classifier.classify(11, "Write notes on the importance of mathematical analysis.")
    assert prop_un.confidence == "UNMAPPED"
    assert prop_un.topic_id is None


def test_acca_mapping_persistence_and_idempotency():
    """Verify that mapped questions exist in question_topic and rerun produces 0 insertions."""
    db = SessionLocal()
    try:
        # Check mapped count in DB
        mapped_count = (
            db.query(question_topic)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 16)
            .count()
        )
        assert mapped_count >= 180, f"Expected at least 180 mapped questions, got {mapped_count}"

        # Verify all mapped topics belong to Course 16 (IDs 315..338)
        topic_ids = [
            r[1] for r in
            db.query(question_topic.c.question_id, question_topic.c.topic_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 16)
            .all()
        ]
        assert all(315 <= tid <= 338 for tid in topic_ids), "Mapped topics must be in range 315..338"

        # Rerun dry-run: 0 new insertions, 0 conflicts
        res = run_acca_mapping(apply_changes=False)
        assert res["new_insertions"] == 0
        assert res["conflicts"] == 0
        assert res["already_mapped"] >= 180
    finally:
        db.close()


def test_acca_intelligence_snapshot_reports_topic_mode(client: TestClient):
    """Verify Course 16 intelligence snapshot transitions to topic mode with calibrated predictions."""
    res = client.get("/api/intelligence/16")
    assert res.status_code == 200
    data = res.json()

    assert data["course"]["id"] == 16
    assert data["course"]["code"] == "SEM2-ACCA"
    assert data["course"]["canonical_code"] == "21MAB102T"
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 24
    assert data["prediction_mode"] == "topic"

    predictions = data.get("predictions", [])
    assert len(predictions) > 0, "Topic predictions must be generated"
    for p in predictions:
        assert p["category"] == "topic"
        assert p["topic_id"] is not None
        assert 315 <= p["topic_id"] <= 338
        assert p["prediction_score"] >= 0.0
        assert p["confidence"] in ("HIGH", "MEDIUM", "LOW")


def test_acca_study_priorities_endpoint(client: TestClient):
    """Verify study priorities endpoint supports all Course 16 identifiers and returns topic plan."""
    for ident in ["16", "SEM2-ACCA", "21MAB102T", "Advanced Calculus and Complex Analysis"]:
        res = client.get(f"/api/study/priorities/{ident}")
        assert res.status_code == 200, f"Failed for identifier: {ident}"
        data = res.json()
        assert data["plan_mode"] == "topic"
        assert data["has_topic_taxonomy"] is True
        assert len(data["priorities"]) > 0


def test_acca_practice_endpoint(client: TestClient):
    """Verify practice questions endpoint returns valid questions for Course 16."""
    res = client.get("/api/practice/16?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("questions", [])) == 10
