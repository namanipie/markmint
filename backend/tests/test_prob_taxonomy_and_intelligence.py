"""
Comprehensive test suite for Course 22: Probability and Statistics (PROB).
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
from backend.services.taxonomy_rules.prob_rules import PROB_TAXONOMY_RULES
from scripts.curriculum.map_prob_questions_to_topics import run_prob_mapping


@pytest.fixture
def client():
    return TestClient(app)


def test_prob_registry_integrity():
    """Verify Course 22 declarative structure and invariants in taxonomy registry."""
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()

    assert registry.has_course(22), "Course 22 must be registered in taxonomy registry"
    entry = registry.get_course(22)

    assert entry.course.id == 22
    assert entry.course.canonical_code == "21MAB201T"
    assert entry.course.code == "SEM2-PROB"
    assert entry.course.name == "Probability and Statistics"
    assert entry.provenance.regulation == "2021"

    # Exactly 5 units
    assert len(entry.units) == 5
    assert [u.number for u in entry.units] == [1, 2, 3, 4, 5]

    # Exactly 25 topics
    total_topics = sum(len(u.topics) for u in entry.units)
    assert total_topics == 25

    # Check topic rules count and topic ID range 414..438
    rules = registry.get_topic_rules(22)
    assert len(rules) == 25
    topic_ids = [r.topic_id for r in rules]
    assert sorted(topic_ids) == list(range(414, 439))


def test_prob_database_validation():
    """Verify declarative definition matches current SQLite database taxonomy for Course 22."""
    registry = get_taxonomy_registry()
    db = SessionLocal()
    try:
        val = registry.validate_against_database(22, db)
        assert val["valid"] is True, f"DB validation failed: {val.get('mismatches')}"
        assert val["units_verified"] == 5
        assert val["topics_verified"] == 25
        assert len(val["mismatches"]) == 0
    finally:
        db.close()


def test_prob_no_cross_course_leakage():
    """Verify zero overlap in topic IDs and unit IDs between Course 22 and other courses."""
    registry = get_taxonomy_registry()
    chem = registry.get_course(2)
    spcm = registry.get_course(13)
    eee = registry.get_course(14)
    acca = registry.get_course(16)
    oodp = registry.get_course(17)
    espcb = registry.get_course(18)
    engmech = registry.get_course(21)
    prob = registry.get_course(22)

    prob_topic_ids = {t.id for u in prob.units for t in u.topics}
    for other in [chem, spcm, eee, acca, oodp, espcb, engmech]:
        other_tids = {t.id for u in other.units for t in u.topics}
        assert prob_topic_ids.isdisjoint(other_tids), f"PROB topic IDs must not overlap with {other.course.name}"

    prob_unit_ids = {u.id for u in prob.units}
    for other in [chem, spcm, eee, acca, oodp, espcb, engmech]:
        other_uids = {u.id for u in other.units}
        assert prob_unit_ids.isdisjoint(other_uids), f"PROB unit IDs must not overlap with {other.course.name}"


def test_prob_classifier_behavior_across_all_units():
    """Verify classifier correctly matches domain prompts across all 5 units with high confidence."""
    classifier = TaxonomyClassifierService(PROB_TAXONOMY_RULES)

    # Unit 1: Bayes' Theorem
    prop1 = classifier.classify(1, "State and prove Bayes' theorem for conditional probability.")
    assert prop1.confidence == "HIGH"
    assert prop1.topic_id == 414

    # Unit 2: Binomial Distribution
    prop2 = classifier.classify(2, "Find the mean of a binomial distribution and determine its parameters.")
    assert prop2.confidence == "HIGH"
    assert prop2.topic_id == 419

    # Unit 3: Small Sample Tests (Student's t-test)
    prop3 = classifier.classify(3, "Explain the procedure for Student's t-test for single mean with an example.")
    assert prop3.confidence == "HIGH"
    assert prop3.topic_id == 426

    # Unit 4: Rank Correlation
    prop4 = classifier.classify(4, "Compute the Spearman's rank correlation coefficient from the given dataset.")
    assert prop4.confidence == "HIGH"
    assert prop4.topic_id == 429

    # Unit 5: Statistical Quality Control
    prop5 = classifier.classify(5, "Explain the concepts of statistical quality control and Shewhart control charts.")
    assert prop5.confidence == "HIGH"
    assert prop5.topic_id == 434


def test_prob_ambiguity_and_guardrail_rejections():
    """Verify conservative matching flags conflicting topics as AMBIGUOUS and ignores unmapped prompts."""
    classifier = TaxonomyClassifierService(PROB_TAXONOMY_RULES)

    # Question spanning both Mean Chart and Range Chart
    composite_text = "Construct the x-bar chart and also construct the r chart for the sample data."
    prop_amb = classifier.classify(10, composite_text)
    assert prop_amb.confidence == "AMBIGUOUS"
    assert prop_amb.topic_id is None
    assert len(prop_amb.candidate_topics) >= 2

    # Generic prompt
    prop_un = classifier.classify(11, "Check all questions carefully and do not write anything on the question paper.")
    assert prop_un.confidence == "UNMAPPED"
    assert prop_un.topic_id is None


def test_prob_mapping_persistence_and_idempotency():
    """Verify that mapped questions exist in question_topic and rerun produces 0 insertions."""
    db = SessionLocal()
    try:
        # Check mapped count in DB
        mapped_count = (
            db.query(question_topic)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 22)
            .count()
        )
        assert mapped_count >= 40, f"Expected at least 40 mapped questions, got {mapped_count}"

        # Verify all mapped topics belong to Course 22 (IDs 414..438)
        topic_ids = [
            r[1] for r in
            db.query(question_topic.c.question_id, question_topic.c.topic_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 22)
            .all()
        ]
        assert all(414 <= tid <= 438 for tid in topic_ids), "Mapped topics must be in range 414..438"

        # Rerun dry-run: 0 new insertions, 0 conflicts
        res = run_prob_mapping(apply_changes=False)
        assert res["new_insertions"] == 0
        assert res["conflicts"] == 0
        assert res["already_mapped"] >= 40
    finally:
        db.close()


def test_prob_intelligence_snapshot_reports_topic_mode(client: TestClient):
    """Verify Course 22 intelligence snapshot transitions to topic mode with calibrated predictions."""
    res = client.get("/api/intelligence/22")
    assert res.status_code == 200
    data = res.json()

    assert data["course"]["id"] == 22
    assert data["course"]["code"] == "SEM2-PROB"
    assert data["course"]["canonical_code"] == "21MAB201T"
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 25
    assert data["prediction_mode"] == "topic"

    predictions = data.get("predictions", [])
    assert len(predictions) > 0, "Topic predictions must be generated"
    for p in predictions:
        assert p["category"] == "topic"
        assert p["topic_id"] is not None
        assert 414 <= p["topic_id"] <= 438
        assert p["prediction_score"] >= 0.0
        assert p["confidence"] in ("HIGH", "MEDIUM", "LOW")


def test_prob_study_priorities_endpoint(client: TestClient):
    """Verify study priorities endpoint supports all Course 22 identifiers and returns topic plan."""
    for ident in ["22", "SEM2-PROB", "21MAB201T", "Probability and Statistics"]:
        res = client.get(f"/api/study/priorities/{ident}")
        assert res.status_code == 200, f"Failed for identifier: {ident}"
        data = res.json()
        assert data["plan_mode"] == "topic"
        assert data["has_topic_taxonomy"] is True
        assert len(data["priorities"]) > 0


def test_prob_practice_endpoint(client: TestClient):
    """Verify practice questions endpoint returns valid questions for Course 22."""
    res = client.get("/api/practice/22?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("questions", [])) == 10
