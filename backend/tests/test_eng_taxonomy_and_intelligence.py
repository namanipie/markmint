"""
Comprehensive test suite for Course 15: Communicative English (ENG).
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
from backend.services.taxonomy_rules.eng_rules import ENG_TAXONOMY_RULES
from scripts.curriculum.map_eng_questions_to_topics import run_eng_mapping


@pytest.fixture
def client():
    return TestClient(app)


def test_eng_registry_integrity():
    """Verify Course 15 declarative structure and invariants in taxonomy registry."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    assert registry.has_course(15), "Course 15 must be registered in taxonomy registry"
    entry = registry.get_course(15)

    assert entry.course.id == 15
    assert entry.course.canonical_code == "21LEH101T"
    assert entry.course.code == "SEM1-ENG"
    assert entry.course.name == "Communicative English"
    assert entry.provenance.regulation == "2021"

    # Exactly 5 units
    assert len(entry.units) == 5
    assert [u.number for u in entry.units] == [1, 2, 3, 4, 5]

    # Exactly 25 topics
    total_topics = sum(len(u.topics) for u in entry.units)
    assert total_topics == 25

    # Check topic rules count and topic ID range 464..488
    rules = registry.get_topic_rules(15)
    assert len(rules) == 25
    topic_ids = [r.topic_id for r in rules]
    assert sorted(topic_ids) == list(range(464, 489))


def test_eng_database_validation():
    """Verify declarative definition matches current SQLite database taxonomy for Course 15."""
    registry = get_taxonomy_registry()
    db = SessionLocal()
    try:
        val = registry.validate_against_database(15, db)
        assert val["valid"] is True, f"DB validation failed: {val.get('mismatches')}"
        assert val["units_verified"] == 5
        assert val["topics_verified"] == 25
        assert len(val["mismatches"]) == 0
    finally:
        db.close()


def test_eng_classifier_unit_rules():
    """Test deterministic classifier with unambiguous synthetic prompts from all 5 units."""
    classifier = TaxonomyClassifierService(ENG_TAXONOMY_RULES)

    cases = [
        # Unit 1
        ("Communication is commonly defined as the imparting or interchange of thoughts.", 464, "HIGH"),
        ("Which of the following is not a communication barrier? Language barrier or noise", 465, "HIGH"),
        ("In which of following, the listener puts himself in place of the speaker? Empathetic listening", 466, "HIGH"),
        ("What is the primary distinction between intensive and extensive reading?", 467, "HIGH"),
        ("Effective business communication relies on the appropriate and efficient use of paralanguage.", 468, "HIGH"),

        # Unit 2
        ("Fill in the blanks with correct form of verb that agrees with the subject: The quality of the mangoes is not good.", 469, "HIGH"),
        ("Choose the correct verb forms for the following sentence: Arun was very upset yesterday because he was ill.", 470, "HIGH"),
        ("Change the following sentence into passive voice: She was crafting an antique.", 471, "HIGH"),
        ("Change the following direct speech into indirect speech: She said, will you come for the party?", 472, "HIGH"),
        ("Identify the degree of comparison for the following sentence: In mountain regions, day travel is better.", 473, "HIGH"),

        # Unit 3
        ("Choose the correct parallel structure: Priya likes running, walking, and hiking.", 474, "HIGH"),
        ("Which of the following is NOT a rule of precis writing? Always have a heading.", 475, "HIGH"),
        ("Draft a letter to the passport office seeking permission for renewal.", 476, "HIGH"),
        ("Typing in all capitals in electronic communication means you are shouting according to netiquette guidelines.", 477, "HIGH"),
        ("Draft a curriculum vitae (CV) accompanied by a job application addressed to The Secretary.", 478, "HIGH"),

        # Unit 4
        ("Which of the following is typically included in an agenda for a meeting?", 479, "HIGH"),
        ("Prepare an investigative report on youngsters losing their lives due to road accidents.", 480, "HIGH"),
        ("The proposal should start with an overview of the main area.", 481, "HIGH"),
        ("Convert the following passage into a flowchart to represent the manufacturing sequence.", 482, "HIGH"),
        ("Choose the appropriate synonym for 'translucent' and the appropriate antonym for 'abstain'.", 483, "HIGH"),

        # Unit 5
        ("Find the odd one out with reference to public speaking and speech delivery.", 484, "HIGH"),
        ("Elaborate on the essential skills for the effective-group discussion.", 485, "HIGH"),
        ("Which of the following series is correct when making a presentation with effective visual aids?", 486, "HIGH"),
        ("Self-plagiarism means reusing a paragraph from a previous paper you wrote without citation.", 487, "HIGH"),
        ("Explain asynchronous communication and its significance in modern workplaces.", 488, "HIGH"),
    ]

    for text, expected_tid, expected_conf in cases:
        proposals = classifier.classify_batch([{"id": 1, "original_text": text}])
        p = proposals[0]
        assert p.topic_id == expected_tid, (
            f"Expected topic {expected_tid} for text '{text}', got {p.topic_id} ({p.topic_name})"
        )
        assert p.confidence == expected_conf


def test_eng_classifier_ambiguity_and_guards():
    """Verify conservative handling for ambiguous questions spanning multiple topics."""
    classifier = TaxonomyClassifierService(ENG_TAXONOMY_RULES)

    ambiguous_prompt = (
        "21. a. What are the major barriers to communication in an organization? "
        "--- OR --- "
        "21. b. Explain the role of kinesics and non-verbal communication in effective leadership."
    )
    props = classifier.classify_batch([{"id": 100, "original_text": ambiguous_prompt}])
    p = props[0]
    assert p.confidence == "AMBIGUOUS", f"Expected AMBIGUOUS for composite question, got {p.confidence}"
    assert p.topic_id is None


def test_eng_mapping_persisted_in_db():
    """Verify that mapped questions exist in SQLite database with valid Course 15 topics."""
    db = SessionLocal()
    try:
        rows = (
            db.query(question_topic.c.question_id, question_topic.c.topic_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 15)
            .all()
        )
        assert len(rows) >= 250, f"Expected at least 250 mapped questions, found {len(rows)}"

        # Every topic_id must be in range 464..488
        valid_topic_ids = set(range(464, 489))
        for qid, tid in rows:
            assert tid in valid_topic_ids, f"Question {qid} mapped to invalid topic {tid}"
    finally:
        db.close()


def test_eng_mapping_idempotence():
    """Verify mapping CLI is strictly idempotent: 0 new insertions, 0 conflicts on re-run."""
    result = run_eng_mapping(apply_changes=False)
    assert result["to_insert"] == 0, f"Expected 0 new insertions on rerun, got {result['to_insert']}"
    assert result["conflicts"] == 0, f"Expected 0 conflicts, got {result['conflicts']}"
    assert result["already_correct"] >= 250, f"Expected >= 250 already correct, got {result['already_correct']}"


def test_eng_zero_cross_course_leakage():
    """Verify no questions from other courses were assigned Course 15 topics."""
    db = SessionLocal()
    try:
        eng_topic_ids = list(range(464, 489))
        leakage = (
            db.query(question_topic.c.question_id, question_topic.c.topic_id, Exam.course_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(question_topic.c.topic_id.in_(eng_topic_ids))
            .filter(Exam.course_id != 15)
            .all()
        )
        assert len(leakage) == 0, f"Detected cross-course leakage: {leakage}"
    finally:
        db.close()


def test_eng_intelligence_snapshot_endpoint(client: TestClient):
    """Verify intelligence snapshot endpoint returns topic-mode payload for Course 15."""
    res = client.get("/api/intelligence/15")
    assert res.status_code == 200
    data = res.json()

    assert data["course"]["id"] == 15
    assert data["course"]["code"] == "SEM1-ENG"
    assert data["course"]["canonical_code"] == "21LEH101T"
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 25
    assert data["prediction_mode"] == "topic"

    predictions = data.get("predictions", [])
    assert len(predictions) > 0, "Topic predictions must be generated"
    for p in predictions:
        assert p["category"] == "topic"
        assert p["topic_id"] is not None
        assert 464 <= p["topic_id"] <= 488
        assert p["prediction_score"] >= 0.0
        assert p["confidence"] in ("HIGH", "MEDIUM", "LOW")


def test_eng_study_priorities_endpoint(client: TestClient):
    """Verify study priorities endpoint supports all Course 15 identifiers and returns topic plan."""
    for ident in ["15", "SEM1-ENG", "21LEH101T", "Communicative English"]:
        res = client.get(f"/api/study/priorities/{ident}")
        assert res.status_code == 200, f"Failed for identifier: {ident}"
        data = res.json()
        assert data["plan_mode"] == "topic"
        assert data["has_topic_taxonomy"] is True
        assert len(data["priorities"]) > 0


def test_eng_practice_endpoint(client: TestClient):
    """Verify practice questions endpoint returns valid questions for Course 15."""
    res = client.get("/api/practice/15?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("questions", [])) == 10
