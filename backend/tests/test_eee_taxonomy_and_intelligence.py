"""
Comprehensive test suite for Course 14: Electrical and Electronics Engineering (EEE).
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
from backend.services.taxonomy_rules.eee_rules import EEE_TAXONOMY_RULES
from scripts.curriculum.map_eee_questions_to_topics import run_eee_mapping


@pytest.fixture
def client():
    return TestClient(app)


def test_eee_registry_integrity():
    """Verify Course 14 declarative structure and invariants in taxonomy registry."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    assert registry.has_course(14), "Course 14 must be registered in taxonomy registry"
    entry = registry.get_course(14)

    assert entry.course.id == 14
    assert entry.course.canonical_code == "21EEB101J"
    assert entry.course.code == "SEM1-EEE"
    assert entry.course.name == "Electrical and Electronics Engineering"
    assert entry.provenance.regulation == "2021"

    # Exactly 5 units
    assert len(entry.units) == 5
    assert [u.number for u in entry.units] == [1, 2, 3, 4, 5]

    # Exactly 35 topics
    total_topics = sum(len(u.topics) for u in entry.units)
    assert total_topics == 35

    # Check topic rules count and topic ID range 280..314
    rules = registry.get_topic_rules(14)
    assert len(rules) == 35
    topic_ids = [r.topic_id for r in rules]
    assert sorted(topic_ids) == list(range(280, 315))


def test_eee_database_validation():
    """Verify declarative definition matches current SQLite database taxonomy for Course 14."""
    registry = get_taxonomy_registry()
    db = SessionLocal()
    try:
        val = registry.validate_against_database(14, db)
        assert val["valid"] is True, f"DB validation failed: {val.get('mismatches')}"
        assert val["units_verified"] == 5
        assert val["topics_verified"] == 35
        assert len(val["mismatches"]) == 0
    finally:
        db.close()


def test_eee_no_cross_course_leakage():
    """Verify zero overlap in topic IDs and unit IDs between Course 14 and Courses 2 & 13."""
    registry = get_taxonomy_registry()
    chem = registry.get_course(2)
    spcm = registry.get_course(13)
    eee = registry.get_course(14)

    eee_topic_ids = {t.id for u in eee.units for t in u.topics}
    chem_topic_ids = {t.id for u in chem.units for t in u.topics}
    spcm_topic_ids = {t.id for u in spcm.units for t in u.topics}

    assert eee_topic_ids.isdisjoint(chem_topic_ids), "EEE topic IDs must not overlap with Chemistry"
    assert eee_topic_ids.isdisjoint(spcm_topic_ids), "EEE topic IDs must not overlap with SPCM"

    eee_unit_ids = {u.id for u in eee.units}
    chem_unit_ids = {u.id for u in chem.units}
    spcm_unit_ids = {u.id for u in spcm.units}

    assert eee_unit_ids.isdisjoint(chem_unit_ids), "EEE unit IDs must not overlap with Chemistry"
    assert eee_unit_ids.isdisjoint(spcm_unit_ids), "EEE unit IDs must not overlap with SPCM"


def test_eee_classifier_behavior_across_all_units():
    """Verify classifier correctly matches domain prompts across all 5 units with high confidence."""
    classifier = TaxonomyClassifierService(EEE_TAXONOMY_RULES)

    # Unit 1: Network Theorems
    prop1 = classifier.classify(1, "State and prove Thevenin's theorem with an illustrative DC circuit.")
    assert prop1.confidence == "HIGH"
    assert prop1.topic_id == 282

    # Unit 2: Karnaugh Map Minimization
    prop2 = classifier.classify(2, "Simplify the following four variable boolean function using Karnaugh map.")
    assert prop2.confidence == "HIGH"
    assert prop2.topic_id == 293

    # Unit 3: Three-Phase Induction Motors
    prop3 = classifier.classify(3, "Explain the construction and working of three-phase induction motor.")
    assert prop3.confidence == "HIGH"
    assert prop3.topic_id == 297

    # Unit 4: Displacement and Position Transducers
    prop4 = classifier.classify(4, "Explain the construction, working principle, and displacement measurement using LVDT.")
    assert prop4.confidence == "HIGH"
    assert prop4.topic_id == 303

    # Unit 5: Electrical Safety and Earthing
    prop5 = classifier.classify(5, "Explain the importance of earthing and describe the pipe earthing method.")
    assert prop5.confidence == "HIGH"
    assert prop5.topic_id == 310


def test_eee_ambiguity_and_guardrail_rejections():
    """Verify conservative matching flags conflicting topics as AMBIGUOUS and ignores unmapped prompts."""
    classifier = TaxonomyClassifierService(EEE_TAXONOMY_RULES)

    # Question with both Chopper and Transformer
    prop_amb = classifier.classify(10, "A chopper converts DC while a transformer changes AC voltage.")
    assert prop_amb.confidence == "AMBIGUOUS"
    assert prop_amb.topic_id is None
    assert len(prop_amb.candidate_topics) >= 2

    # Question with no electrical keywords
    prop_un = classifier.classify(11, "Please answer all questions carefully on the answer sheet.")
    assert prop_un.confidence == "UNMAPPED"
    assert prop_un.topic_id is None


def test_eee_mapping_persistence_and_idempotency():
    """Verify that mapped questions exist in question_topic and rerun produces 0 insertions."""
    db = SessionLocal()
    try:
        # Check mapped count in DB
        mapped_count = (
            db.query(question_topic)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 14)
            .count()
        )
        assert mapped_count >= 400, f"Expected at least 400 mapped questions, got {mapped_count}"

        # Verify all mapped topics belong to Course 14 (IDs 280..314)
        topic_ids = [
            r[1] for r in
            db.query(question_topic.c.question_id, question_topic.c.topic_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 14)
            .all()
        ]
        assert all(280 <= tid <= 314 for tid in topic_ids), "Mapped topics must be in range 280..314"

        # Rerun dry-run: 0 new insertions, 0 conflicts
        res = run_eee_mapping(apply_changes=False)
        assert res["new_insertions"] == 0
        assert res["conflicts"] == 0
        assert res["already_mapped"] >= 400
    finally:
        db.close()


def test_eee_intelligence_snapshot_reports_topic_mode(client: TestClient):
    """Verify Course 14 intelligence snapshot transitions to topic mode with calibrated predictions."""
    res = client.get("/api/intelligence/14")
    assert res.status_code == 200
    data = res.json()

    assert data["course"]["id"] == 14
    assert data["course"]["code"] == "SEM1-EEE"
    assert data["course"]["canonical_code"] == "21EEB101J"
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 35
    assert data["prediction_mode"] == "topic"

    predictions = data.get("predictions", [])
    assert len(predictions) > 0, "Topic predictions must be generated"
    for p in predictions:
        assert p["category"] == "topic"
        assert p["topic_id"] is not None
        assert 280 <= p["topic_id"] <= 314
        assert p["prediction_score"] >= 0.0
        assert p["confidence"] in ("HIGH", "MEDIUM", "LOW")


def test_eee_study_priorities_endpoint(client: TestClient):
    """Verify study priorities endpoint supports all Course 14 identifiers and returns topic plan."""
    for ident in ["14", "SEM1-EEE", "21EEB101J", "Electrical and Electronics Engineering"]:
        res = client.get(f"/api/study/priorities/{ident}")
        assert res.status_code == 200, f"Failed for identifier: {ident}"
        data = res.json()
        assert data["plan_mode"] == "topic"
        assert data["has_topic_taxonomy"] is True
        assert len(data["priorities"]) > 0


def test_eee_practice_endpoint(client: TestClient):
    """Verify practice questions endpoint returns valid questions for Course 14."""
    res = client.get("/api/practice/14?limit=15")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("questions", [])) == 15
