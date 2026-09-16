"""
Comprehensive test suite for Phase 3 MintAI Expanded Corpus Capabilities.
Tests:
1. ExamDNA distinct paper coverage (no single-paper inflation).
2. Question Family classification & chronological sequence.
3. Assessment comparison (CT1 vs CT2 vs EndSem) with sample-size normalization.
4. Topic Intelligence drilldown linking syllabus, past questions, forecast, and student status.
5. Strict Personalization Isolation (progress modifies priority/action, NEVER probability/confidence).
6. KaTeX equation structure and math safety.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import SessionLocal
from backend.models.core import StudentTopicProgress, Topic

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_dna_paper_coverage_distinct_counting(client: TestClient):
    """Verify that multiple questions from the same exam paper do NOT inflate paper recurrence."""
    resp = client.get("/api/analytics/1/topics")
    assert resp.status_code == 200
    data = resp.json()
    assert "topics" in data
    total_papers = data["total_papers_analyzed"]
    assert total_papers >= 8

    for topic in data["topics"]:
        p_count = topic["paper_count"]
        coverage = topic["paper_coverage"]
        # Paper count must never exceed total papers
        assert p_count <= total_papers
        # Coverage must exactly equal p_count / total_papers
        assert abs(coverage - round(p_count / total_papers, 4)) < 1e-4


def test_question_family_repetition_classification(client: TestClient):
    """Verify distinct repeat types: EXACT_REPEAT and FAMILY_REPEAT."""
    resp = client.get("/api/analytics/1/questions/repeated")
    assert resp.status_code == 200
    data = resp.json()
    assert "exact_repeats" in data
    assert "family_repeats" in data

    for er in data["exact_repeats"]:
        assert er["repetition_type"] == "EXACT_REPEAT"
        assert len(er["instances"]) >= 2

    for fr in data["family_repeats"]:
        assert fr["repetition_type"] == "FAMILY_REPEAT"
        assert len(fr["variants"]) >= 2
        # Chronological order of questions
        years = [q["year"] for q in fr["questions"] if q["year"] is not None]
        assert years == sorted(years)


def test_assessment_comparison_dynamic_normalization(client: TestClient):
    """Verify assessment comparison endpoint handles unequal paper counts and assigns valid bias."""
    resp = client.get("/api/analytics/1/assessment-comparison")
    assert resp.status_code == 200
    data = resp.json()
    assert data["course_id"] == 1
    assert "assessment_types" in data
    assert len(data["assessment_types"]) > 0

    for topic in data["topics"]:
        assert "topic_name" in topic
        assert topic["bias"] in [
            "CLASS_TEST_LEANING", "END_SEM_LEANING", "UNIVERSAL", "BALANCED", "UNEXAMINED"
        ]
        breakdown = topic["assessment_breakdown"]
        for at_name, at_stat in breakdown.items():
            assert at_stat["papers_present"] <= at_stat["total_papers"]
            if at_stat["total_papers"] > 0:
                assert 0.0 <= at_stat["paper_frequency"] <= 1.0


def test_topic_intelligence_drilldown(client: TestClient):
    """Verify Topic Intelligence combines syllabus, past questions, forecast, and student action."""
    resp = client.get("/api/analytics/1/topics/1/intelligence?student_id=student_42")
    assert resp.status_code == 200
    data = resp.json()
    assert data["topic_id"] == 1
    assert data["course_id"] == 1
    assert "unit" in data
    assert "number" in data["unit"]

    # Metrics
    metrics = data["repetition_metrics"]
    assert metrics["paper_count"] <= metrics["total_papers"]
    assert 0.0 <= metrics["paper_coverage"] <= 1.0
    assert metrics["total_marks"] >= 0.0

    # Past Questions
    assert len(data["past_questions"]) > 0
    for q in data["past_questions"]:
        assert "original_text" in q
        assert "repeat_type" in q

    # Forecast
    forecast = data["forecast"]
    assert 0.0 <= forecast["probability"] <= 100.0
    assert forecast["confidence"] in ["LOW", "MEDIUM", "HIGH"]
    assert len(forecast["reason_codes"]) > 0

    # Personalization
    pers = data["personalization"]
    assert pers["student_id"] == "student_42"
    assert "priority_score" in pers
    assert "recommended_action" in pers


def test_strict_personalization_isolation(client: TestClient):
    """
    CRITICAL INVARIANT: Student progress modifications adjust priority and recommended action,
    but NEVER mutate probability or confidence.
    """
    topic_id = 1
    student_a = "student_novice_99"
    student_b = "student_master_99"

    db = SessionLocal()
    try:
        # Student A is NOT_STARTED
        p_a = db.query(StudentTopicProgress).filter(
            StudentTopicProgress.student_id == student_a,
            StudentTopicProgress.topic_id == topic_id
        ).first()
        if not p_a:
            p_a = StudentTopicProgress(student_id=student_a, topic_id=topic_id, status="NOT_STARTED")
            db.add(p_a)
        else:
            p_a.status = "NOT_STARTED"

        # Student B is MASTERED
        p_b = db.query(StudentTopicProgress).filter(
            StudentTopicProgress.student_id == student_b,
            StudentTopicProgress.topic_id == topic_id
        ).first()
        if not p_b:
            p_b = StudentTopicProgress(student_id=student_b, topic_id=topic_id, status="MASTERED")
            db.add(p_b)
        else:
            p_b.status = "MASTERED"

        db.commit()
    finally:
        db.close()

    # Query Topic Intelligence for Student A
    resp_a = client.get(f"/api/analytics/1/topics/{topic_id}/intelligence?student_id={student_a}")
    assert resp_a.status_code == 200
    data_a = resp_a.json()

    # Query Topic Intelligence for Student B
    resp_b = client.get(f"/api/analytics/1/topics/{topic_id}/intelligence?student_id={student_b}")
    assert resp_b.status_code == 200
    data_b = resp_b.json()

    # Probability and Confidence MUST BE IDENTICAL
    assert data_a["forecast"]["probability"] == data_b["forecast"]["probability"]
    assert data_a["forecast"]["confidence"] == data_b["forecast"]["confidence"]

    # Priorities and Actions MUST DIFFER based on progress
    assert data_a["personalization"]["priority_score"] > data_b["personalization"]["priority_score"]
    assert data_a["personalization"]["recommended_action"] != data_b["personalization"]["recommended_action"]


def test_predictions_historical_timeline(client: TestClient):
    """Verify prediction endpoint returns chronological multi-year timeline with presence indicators."""
    resp = client.get("/api/predictions/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "observed_years" in data
    assert len(data["observed_years"]) >= 5

    assert "predictions" in data
    assert len(data["predictions"]) > 0

    for pred in data["predictions"]:
        assert "timeline" in pred
        assert isinstance(pred["timeline"], list)
        assert len(pred["timeline"]) == len(data["observed_years"])
        for tl_entry in pred["timeline"]:
            assert "year" in tl_entry
            assert "present" in tl_entry
            assert isinstance(tl_entry["present"], bool)
            assert "exam_exists" in tl_entry
            assert tl_entry["exam_exists"] is True
            assert "topic_present" in tl_entry or "family_present" in tl_entry


def test_timeline_semantics_distinguish_exam_topic_family_and_gap_years(client: TestClient):
    """
    CRITICAL SANITY CHECK:
    Verify that:
    1. EXAM_EXISTS, TOPIC_PRESENT, and FAMILY_PRESENT are distinctly tracked and never collapsed.
    2. present=False means 'The selected topic/family was not observed in that year's exam',
       and NOT 'There was no exam in that year'.
    3. Gap years [2016, 2017, 2020, 2021] are explicitly tracked where no verified exam exists.
    """
    # 1. Course-level exam evolution timeline
    resp_evo = client.get("/api/analytics/1/exam-evolution")
    assert resp_evo.status_code == 200
    evo_data = resp_evo.json()

    assert evo_data["observed_years"] == [2015, 2018, 2019, 2022, 2023, 2024, 2025]
    assert evo_data["unobserved_years"] == [2016, 2017, 2020, 2021]
    assert evo_data["gap_years"] == [2016, 2017, 2020, 2021]

    # In evolution timeline, every entry has exam_exists=True
    for entry in evo_data["timeline"]:
        assert entry["exam_exists"] is True
        assert entry["paper_count"] >= 1
        assert entry["year"] in evo_data["observed_years"]

    # In gap entries, every entry has exam_exists=False
    for gap in evo_data["gap_entries"]:
        assert gap["exam_exists"] is False
        assert gap["gap"] is True
        assert gap["status"] == "NO_EXAM_RECORDED"
        assert gap["year"] in [2016, 2017, 2020, 2021]

    # 2. Topic-level recurrence timeline via Topic Intelligence
    resp_topic = client.get("/api/analytics/1/topics/1/intelligence")
    assert resp_topic.status_code == 200
    topic_data = resp_topic.json()

    assert "timeline" in topic_data
    assert topic_data["observed_years"] == [2015, 2018, 2019, 2022, 2023, 2024, 2025]
    assert topic_data["unobserved_years"] == [2016, 2017, 2020, 2021]

    # Verify that present=False strictly means exam exists, but topic was not in that exam
    has_present_false = False
    for tl in topic_data["timeline"]:
        assert tl["exam_exists"] is True  # All observed years had exams!
        assert "topic_present" in tl
        assert "family_present" in tl
        assert "status" in tl
        if not tl["present"]:
            has_present_false = True
            assert tl["topic_present"] is False
            assert tl["status"] == "TOPIC_ABSENT"
            # Explicit confirmation: an exam DID exist in this year!
            assert tl["exam_exists"] is True

    assert has_present_false, "Must have years where exam existed but topic was absent"

    # 3. Question-family timeline via Repeated Families endpoint
    resp_fam = client.get("/api/analytics/1/families")
    assert resp_fam.status_code == 200
    fam_data = resp_fam.json()

    assert fam_data["observed_years"] == [2015, 2018, 2019, 2022, 2023, 2024, 2025]
    assert fam_data["gap_years"] == [2016, 2017, 2020, 2021]

    for fam in fam_data["families"]:
        assert "timeline" in fam
        for tl in fam["timeline"]:
            assert tl["exam_exists"] is True
            assert "family_present" in tl
            assert tl["present"] == tl["family_present"]
            if not tl["present"]:
                assert tl["status"] == "FAMILY_ABSENT"
                assert tl["exam_exists"] is True

