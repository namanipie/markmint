"""
Comprehensive test suite for Course 23: Building Materials in the Built Environment (BLDMAT).
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
from backend.services.taxonomy_rules.bldmat_rules import BLDMAT_TAXONOMY_RULES
from scripts.curriculum.map_bldmat_questions_to_topics import run_bldmat_mapping


@pytest.fixture
def client():
    return TestClient(app)


def test_bldmat_registry_integrity():
    """Verify Course 23 declarative structure and invariants in taxonomy registry."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    assert registry.has_course(23), "Course 23 must be registered in taxonomy registry"
    entry = registry.get_course(23)

    assert entry.course.id == 23
    assert entry.course.canonical_code == "21CEB101T"
    assert entry.course.code == "SEM2-BLDMAT"
    assert entry.course.name == "Building Materials in the Built Environment"
    assert entry.provenance.regulation == "2021"

    # Exactly 5 units
    assert len(entry.units) == 5
    assert [u.number for u in entry.units] == [1, 2, 3, 4, 5]

    # Exactly 25 topics
    total_topics = sum(len(u.topics) for u in entry.units)
    assert total_topics == 25

    # Check topic rules count and topic ID range 439..463
    rules = registry.get_topic_rules(23)
    assert len(rules) == 25
    topic_ids = [r.topic_id for r in rules]
    assert sorted(topic_ids) == list(range(439, 464))


def test_bldmat_database_validation():
    """Verify declarative definition matches current SQLite database taxonomy for Course 23."""
    registry = get_taxonomy_registry()
    db = SessionLocal()
    try:
        val = registry.validate_against_database(23, db)
        assert val["valid"] is True, f"DB validation failed: {val.get('mismatches')}"
        assert val["units_verified"] == 5
        assert val["topics_verified"] == 25
        assert len(val["mismatches"]) == 0
    finally:
        db.close()


def test_bldmat_classifier_unit_rules():
    """Test deterministic classifier with unambiguous synthetic prompts from all 5 units."""
    classifier = TaxonomyClassifierService(BLDMAT_TAXONOMY_RULES)

    cases = [
        # Unit 1
        ("Give a detailed note on testing of stones.", 439, "HIGH"),
        ("In which bond brick is laid with its length in the direction of a wall? Flemish bond or English bond", 440, "HIGH"),
        ("Explain the dry manufacturing process of cement with neat sketch.", 441, "HIGH"),
        ("What is the value of specific gravity commonly used for ordinary Portland cement?", 442, "HIGH"),
        ("Discuss different types of steel and its uses. Mild steel and TMT bars.", 443, "HIGH"),

        # Unit 2
        ("Which paint defect is characterized by the peeling or flaking of the top layer of paint?", 444, "HIGH"),
        ("Shellac is a natural resin commonly used as a varnish base.", 445, "HIGH"),
        ("Compound added for green tinted glass: Iron oxide in glass.", 446, "HIGH"),
        ("PVC is a type of thermoplastic used in construction.", 447, "HIGH"),
        ("Write a detailed note on the treatment of building against dampness by interposing damp proof course.", 448, "HIGH"),

        # Unit 3
        ("Explain the cavity wall with neat sketches.", 449, "HIGH"),
        ("Explain the different types of stairs with neat sketch.", 450, "HIGH"),
        ("Write short notes on fire resisting properties of common building material.", 451, "HIGH"),
        ("Explain the concept of fire alarm systems in buildings in details.", 452, "HIGH"),
        ("Write short notes on anti termite treatment.", 453, "HIGH"),

        # Unit 4
        ("In ferro-cement concrete the reinforcement used is wire mesh.", 454, "HIGH"),
        ("Explain the construction procedure, applications, advantages, and disadvantages of ferrocement.", 455, "HIGH"),
        ("A common application of soil-cement blocks made from fly ash.", 456, "HIGH"),
        ("Explain the manufacture and properties of gypsum board and plaster of paris.", 457, "HIGH"),
        ("How can agro-waste be used in building, and why is it useful?", 458, "HIGH"),

        # Unit 5
        ("A zero building produces enough energy to meet its own annual energy consumption requirement.", 459, "HIGH"),
        ("Explain the application of green building rating systems in building certification and GRIHA rating.", 460, "HIGH"),
        ("Explain stack and wind effects in natural ventilation.", 461, "HIGH"),
        ("What does an AQI value of 44 signify about air quality?", 462, "HIGH"),
        ("What problems can arise from moisture intrusion in buildings?", 463, "HIGH"),
    ]

    for text, expected_tid, expected_conf in cases:
        proposals = classifier.classify_batch([{"id": 1, "original_text": text}])
        p = proposals[0]
        assert p.topic_id == expected_tid, (
            f"Expected topic {expected_tid} for text '{text}', got {p.topic_id} ({p.topic_name})"
        )
        assert p.confidence == expected_conf


def test_bldmat_classifier_ambiguity_and_guards():
    """Verify conservative handling for ambiguous questions spanning multiple topics."""
    classifier = TaxonomyClassifierService(BLDMAT_TAXONOMY_RULES)

    ambiguous_prompt = (
        "21. a. Give a detailed note on testing of stones. "
        "--- OR --- "
        "21. b. Explain the dry manufacturing process of cement with neat sketch."
    )
    props = classifier.classify_batch([{"id": 100, "original_text": ambiguous_prompt}])
    p = props[0]
    assert p.confidence == "AMBIGUOUS", f"Expected AMBIGUOUS for composite question, got {p.confidence}"
    assert p.topic_id is None


def test_bldmat_mapping_persisted_in_db():
    """Verify that mapped questions exist in SQLite database with valid Course 23 topics."""
    db = SessionLocal()
    try:
        rows = (
            db.query(question_topic.c.question_id, question_topic.c.topic_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 23)
            .all()
        )
        assert len(rows) >= 70, f"Expected at least 70 mapped questions, found {len(rows)}"

        # Every topic_id must be in range 439..463
        valid_topic_ids = set(range(439, 464))
        for qid, tid in rows:
            assert tid in valid_topic_ids, f"Question {qid} mapped to invalid topic {tid}"
    finally:
        db.close()


def test_bldmat_mapping_idempotence():
    """Verify mapping CLI is strictly idempotent: 0 new insertions, 0 conflicts on re-run."""
    result = run_bldmat_mapping(apply_changes=False)
    assert result["to_insert"] == 0, f"Expected 0 new insertions on rerun, got {result['to_insert']}"
    assert result["conflicts"] == 0, f"Expected 0 conflicts, got {result['conflicts']}"
    assert result["already_correct"] >= 70, f"Expected >= 70 already correct, got {result['already_correct']}"


def test_bldmat_zero_cross_course_leakage():
    """Verify no questions from other courses were assigned Course 23 topics."""
    db = SessionLocal()
    try:
        bldmat_topic_ids = list(range(439, 464))
        leakage = (
            db.query(question_topic.c.question_id, question_topic.c.topic_id, Exam.course_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(question_topic.c.topic_id.in_(bldmat_topic_ids))
            .filter(Exam.course_id != 23)
            .all()
        )
        assert len(leakage) == 0, f"Detected cross-course leakage: {leakage}"
    finally:
        db.close()


def test_bldmat_intelligence_snapshot_endpoint(client: TestClient):
    """Verify intelligence snapshot endpoint returns topic-mode payload for Course 23."""
    res = client.get("/api/intelligence/23")
    assert res.status_code == 200
    data = res.json()

    assert data["course"]["id"] == 23
    assert data["course"]["code"] == "SEM2-BLDMAT"
    assert data["course"]["canonical_code"] == "21CEB101T"
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 25
    assert data["prediction_mode"] == "topic"

    predictions = data.get("predictions", [])
    assert len(predictions) > 0, "Topic predictions must be generated"
    for p in predictions:
        assert p["category"] == "topic"
        assert p["topic_id"] is not None
        assert 439 <= p["topic_id"] <= 463
        assert p["prediction_score"] >= 0.0
        assert p["confidence"] in ("HIGH", "MEDIUM", "LOW")


def test_bldmat_study_priorities_endpoint(client: TestClient):
    """Verify study priorities endpoint supports all Course 23 identifiers and returns topic plan."""
    for ident in ["23", "SEM2-BLDMAT", "21CEB101T", "Building Materials in the Built Environment"]:
        res = client.get(f"/api/study/priorities/{ident}")
        assert res.status_code == 200, f"Failed for identifier: {ident}"
        data = res.json()
        assert data["plan_mode"] == "topic"
        assert data["has_topic_taxonomy"] is True
        assert len(data["priorities"]) > 0


def test_bldmat_practice_endpoint(client: TestClient):
    """Verify practice questions endpoint returns valid questions for Course 23."""
    res = client.get("/api/practice/23?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("questions", [])) == 10
