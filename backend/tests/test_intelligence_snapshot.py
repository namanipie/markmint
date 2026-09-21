import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_intelligence_snapshot_calculus_ready():
    """Verify calculus course 1 produces a fully populated READY intelligence snapshot."""
    res = client.get("/api/intelligence/1")
    assert res.status_code == 200
    data = res.json()

    assert data["data_availability_status"] == "READY"
    assert data["course"]["id"] == 1
    assert data["course"]["canonical_code"] == "21MAB101T"
    assert data["exam_history"]["total_papers"] >= 1
    assert len(data["available_assessment_types"]) > 0

    # Predictions check
    assert len(data["predictions"]) > 0
    top = data["predictions"][0]
    assert "name" in top
    assert "probability" in top
    assert "confidence" in top
    assert "reason_codes" in top
    assert "explanation" in top
    assert isinstance(top["reason_codes"], list)

    # Study priorities check
    assert len(data["study_priorities"]) > 0
    assert "priority" in data["study_priorities"][0]

    # Coverage summary check
    assert data["coverage_summary"] is not None
    assert "student_preparation_coverage" in data["coverage_summary"]

    # Metadata check
    assert "model_version" in data["metadata"]
    assert "engine_version" in data["metadata"]


def test_intelligence_snapshot_programming_ready():
    """Verify programming course 5 (20 exams) returns READY state with valid evidence."""
    res = client.get("/api/intelligence/5")
    assert res.status_code == 200
    data = res.json()

    assert data["data_availability_status"] == "READY"
    assert data["course"]["id"] == 5
    assert data["exam_history"]["total_papers"] >= 20


def test_intelligence_snapshot_unmatched_guardrail():
    """Verify unmatched subject returns UNMATCHED state without error or prediction call."""
    res = client.get("/api/intelligence/aeros-1-3")
    assert res.status_code == 200
    data = res.json()

    assert data["data_availability_status"] == "UNMATCHED"
    assert data["course"] is None
    assert len(data["predictions"]) == 0


def test_intelligence_snapshot_ambiguous_guardrail():
    """Verify ambiguous subject returns AMBIGUOUS state with candidate notes and zero predictions."""
    res = client.get("/api/intelligence/aeros-2-3")
    assert res.status_code == 200
    data = res.json()

    assert data["data_availability_status"] == "AMBIGUOUS"
    assert data["course"] is None
    assert "General Biology" in (data["curriculum"]["notes"] or "")
    assert len(data["predictions"]) == 0


def test_historical_questions_endpoint():
    """Verify historical questions for course 1 return chronological questions with metadata."""
    res = client.get("/api/intelligence/1/questions?limit=10")
    assert res.status_code == 200
    data = res.json()

    assert data["course_id"] == 1
    assert data["total_returned"] > 0
    q = data["questions"][0]
    assert "question_number" in q
    assert "original_text" in q
    assert "marks" in q
    assert "year" in q
    assert "assessment_type" in q


def test_model_performance_endpoint():
    """Verify model-performance returns real evaluation metrics without subjective rankings."""
    res = client.get("/api/intelligence/model-performance")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "COMPLETED"
    assert "methodology" in data
    assert "model_version" in data
    assert isinstance(data["evaluations"], list)
    if data["evaluations"]:
        ev = data["evaluations"][0]
        assert "model" in ev
        assert "metrics" in ev
        assert "target_year" in ev


def test_corpus_health_endpoint():
    """Verify corpus-health returns counts and quality status."""
    res = client.get("/api/intelligence/corpus-health")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "HEALTHY"
    entities = data["corpus_entities"]
    assert entities["courses"] >= 10
    assert entities["exams"] >= 8
    assert entities["questions"] >= 200
    assert "curriculum_mappings" in data
    assert data["curriculum_mappings"]["total"] == 2810
