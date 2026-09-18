"""
Comprehensive test suite for Course 18: Electronic System and PCB Design (ESPCB).
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
from backend.services.taxonomy_rules.espcb_rules import ESPCB_TAXONOMY_RULES
from scripts.curriculum.map_espcb_questions_to_topics import run_espcb_mapping


@pytest.fixture
def client():
    return TestClient(app)


def test_espcb_registry_integrity():
    """Verify Course 18 declarative structure and invariants in taxonomy registry."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    assert registry.has_course(18), "Course 18 must be registered in taxonomy registry"
    entry = registry.get_course(18)

    assert entry.course.id == 18
    assert entry.course.canonical_code == "21ECC101J"
    assert entry.course.code == "SEM2-ESPCB"
    assert entry.course.name == "Electronic System and PCB Design"
    assert entry.provenance.regulation == "2021"

    # Exactly 5 units
    assert len(entry.units) == 5
    assert [u.number for u in entry.units] == [1, 2, 3, 4, 5]

    # Exactly 25 topics
    total_topics = sum(len(u.topics) for u in entry.units)
    assert total_topics == 25

    # Check topic rules count and topic ID range 364..388
    rules = registry.get_topic_rules(18)
    assert len(rules) == 25
    topic_ids = [r.topic_id for r in rules]
    assert sorted(topic_ids) == list(range(364, 389))


def test_espcb_database_validation():
    """Verify declarative definition matches current SQLite database taxonomy for Course 18."""
    registry = get_taxonomy_registry()
    db = SessionLocal()
    try:
        val = registry.validate_against_database(18, db)
        assert val["valid"] is True, f"DB validation failed: {val.get('mismatches')}"
        assert val["units_verified"] == 5
        assert val["topics_verified"] == 25
        assert len(val["mismatches"]) == 0
    finally:
        db.close()


def test_espcb_no_cross_course_leakage():
    """Verify zero overlap in topic IDs and unit IDs between Course 18 and other courses (2, 13, 14, 16, 17)."""
    registry = get_taxonomy_registry()
    chem = registry.get_course(2)
    spcm = registry.get_course(13)
    eee = registry.get_course(14)
    acca = registry.get_course(16)
    oodp = registry.get_course(17)
    espcb = registry.get_course(18)

    espcb_topic_ids = {t.id for u in espcb.units for t in u.topics}
    chem_topic_ids = {t.id for u in chem.units for t in u.topics}
    spcm_topic_ids = {t.id for u in spcm.units for t in u.topics}
    eee_topic_ids = {t.id for u in eee.units for t in u.topics}
    acca_topic_ids = {t.id for u in acca.units for t in u.topics}
    oodp_topic_ids = {t.id for u in oodp.units for t in u.topics}

    assert espcb_topic_ids.isdisjoint(chem_topic_ids), "ESPCB topic IDs must not overlap with Chemistry"
    assert espcb_topic_ids.isdisjoint(spcm_topic_ids), "ESPCB topic IDs must not overlap with SPCM"
    assert espcb_topic_ids.isdisjoint(eee_topic_ids), "ESPCB topic IDs must not overlap with EEE"
    assert espcb_topic_ids.isdisjoint(acca_topic_ids), "ESPCB topic IDs must not overlap with ACCA"
    assert espcb_topic_ids.isdisjoint(oodp_topic_ids), "ESPCB topic IDs must not overlap with OODP"

    espcb_unit_ids = {u.id for u in espcb.units}
    chem_unit_ids = {u.id for u in chem.units}
    spcm_unit_ids = {u.id for u in spcm.units}
    eee_unit_ids = {u.id for u in eee.units}
    acca_unit_ids = {u.id for u in acca.units}
    oodp_unit_ids = {u.id for u in oodp.units}

    assert espcb_unit_ids.isdisjoint(chem_unit_ids), "ESPCB unit IDs must not overlap with Chemistry"
    assert espcb_unit_ids.isdisjoint(spcm_unit_ids), "ESPCB unit IDs must not overlap with SPCM"
    assert espcb_unit_ids.isdisjoint(eee_unit_ids), "ESPCB unit IDs must not overlap with EEE"
    assert espcb_unit_ids.isdisjoint(acca_unit_ids), "ESPCB unit IDs must not overlap with ACCA"
    assert espcb_unit_ids.isdisjoint(oodp_unit_ids), "ESPCB unit IDs must not overlap with OODP"


def test_espcb_classifier_behavior_across_all_units():
    """Verify classifier correctly matches domain prompts across all 5 units with high confidence."""
    classifier = TaxonomyClassifierService(ESPCB_TAXONOMY_RULES)

    # Unit 1: Drift, Diffusion Currents, and Einstein Relationship
    prop1 = classifier.classify(1, "State and explain the Einstein relationship for carrier diffusion and drift in a semiconductor.")
    assert prop1.confidence == "HIGH"
    assert prop1.topic_id == 366

    # Unit 2: Thyristor and SCR
    prop2 = classifier.classify(2, "Explain the two transistor analogy of silicon controlled rectifier with a neat circuit diagram.")
    assert prop2.confidence == "HIGH"
    assert prop2.topic_id == 371

    # Unit 3: Switched Mode Power Supply
    prop3 = classifier.classify(3, "Explain the circuit operation and classification of smps with flyback converter.")
    assert prop3.confidence == "HIGH"
    assert prop3.topic_id == 376

    # Unit 4: Component Placement and Routing
    prop4 = classifier.classify(4, "Explain the electrical design consideration of pcb regarding trace width calculation and routing.")
    assert prop4.confidence == "HIGH"
    assert prop4.topic_id == 383

    # Unit 5: Signal Integrity and Cross-talk
    prop5 = classifier.classify(5, "Discuss the causes of reflections in digital pcb and how to minimize cross talk in pcb.")
    assert prop5.confidence == "HIGH"
    assert prop5.topic_id == 386


def test_espcb_ambiguity_and_guardrail_rejections():
    """Verify conservative matching flags conflicting topics as AMBIGUOUS and ignores unmapped prompts."""
    classifier = TaxonomyClassifierService(ESPCB_TAXONOMY_RULES)

    # Question spanning both Doping (Topic 364) and Fermi Level / Carrier Concentration (Topic 365)
    composite_text = "A silicon bar is doped with donor impurities and calculate the intrinsic carrier concentration and fermi energy level."
    prop_amb = classifier.classify(10, composite_text)
    assert prop_amb.confidence == "AMBIGUOUS"
    assert prop_amb.topic_id is None
    assert len(prop_amb.candidate_topics) >= 2

    # Generic prompt
    prop_un = classifier.classify(11, "Enter your registration number and department on the examination booklet.")
    assert prop_un.confidence == "UNMAPPED"
    assert prop_un.topic_id is None


def test_espcb_mapping_persistence_and_idempotency():
    """Verify that mapped questions exist in question_topic and rerun produces 0 insertions."""
    db = SessionLocal()
    try:
        # Check mapped count in DB
        mapped_count = (
            db.query(question_topic)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 18)
            .count()
        )
        assert mapped_count >= 130, f"Expected at least 130 mapped questions, got {mapped_count}"

        # Verify all mapped topics belong to Course 18 (IDs 364..388)
        topic_ids = [
            r[1] for r in
            db.query(question_topic.c.question_id, question_topic.c.topic_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 18)
            .all()
        ]
        assert all(364 <= tid <= 388 for tid in topic_ids), "Mapped topics must be in range 364..388"

        # Rerun dry-run: 0 new insertions, 0 conflicts
        res = run_espcb_mapping(apply_changes=False)
        assert res["new_insertions"] == 0
        assert res["conflicts"] == 0
        assert res["already_mapped"] >= 130
    finally:
        db.close()


def test_espcb_intelligence_snapshot_reports_topic_mode(client: TestClient):
    """Verify Course 18 intelligence snapshot transitions to topic mode with calibrated predictions."""
    res = client.get("/api/intelligence/18")
    assert res.status_code == 200
    data = res.json()

    assert data["course"]["id"] == 18
    assert data["course"]["code"] == "SEM2-ESPCB"
    assert data["course"]["canonical_code"] == "21ECC101J"
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 25
    assert data["prediction_mode"] == "topic"

    predictions = data.get("predictions", [])
    assert len(predictions) > 0, "Topic predictions must be generated"
    for p in predictions:
        assert p["category"] == "topic"
        assert p["topic_id"] is not None
        assert 364 <= p["topic_id"] <= 388
        assert p["prediction_score"] >= 0.0
        assert p["confidence"] in ("HIGH", "MEDIUM", "LOW")


def test_espcb_study_priorities_endpoint(client: TestClient):
    """Verify study priorities endpoint supports all Course 18 identifiers and returns topic plan."""
    for ident in ["18", "SEM2-ESPCB", "21ECC101J", "Electronic System and PCB Design"]:
        res = client.get(f"/api/study/priorities/{ident}")
        assert res.status_code == 200, f"Failed for identifier: {ident}"
        data = res.json()
        assert data["plan_mode"] == "topic"
        assert data["has_topic_taxonomy"] is True
        assert len(data["priorities"]) > 0


def test_espcb_practice_endpoint(client: TestClient):
    """Verify practice questions endpoint returns valid questions for Course 18."""
    res = client.get("/api/practice/18?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("questions", [])) == 10
