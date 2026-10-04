import pytest
from fastapi.testclient import TestClient

from backend.core.database import SessionLocal, get_db
from backend.main import app
from backend.models.core import Course, Exam, Section, Question, Topic


@pytest.fixture(scope="module")
def prod_client():
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_mintai_historical_provenance_distinguishability(prod_client: TestClient):
    """Verify that when historical exam questions exist, provenance is strictly HISTORICAL_EVIDENCE."""
    # Course 1 is Calculus and Linear Algebra with extensive historical exams
    res = prod_client.post(
        "/api/intelligence/generate-questions",
        json={
            "topic": "Matrices",
            "course_id": 1,
            "cycle": "ALL",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["topic"] == "Matrices"
    assert data["course_id"] == 1
    assert data["provenance"] == "HISTORICAL_EVIDENCE"
    assert data["is_synthetic"] is False
    assert data["evidence_count"] > 0
    assert len(data["questions"]) > 0

    # Verify each question carries explicit historical provenance
    for q in data["questions"]:
        assert q["provenance"] == "HISTORICAL_EVIDENCE"
        assert q["is_synthetic"] is False
        assert q["exam_year"] is not None
        assert q["exam_year"] > 2000
        assert "Verified Historical SRM Exam" in q["source_label"]


def test_mintai_temporal_cutoff_enforcement(prod_client: TestClient):
    """Verify that temporal cutoff strictly prevents leaking questions from cutoff_year or later."""
    cutoff = 2023
    res = prod_client.post(
        "/api/intelligence/generate-questions",
        json={
            "topic": "Eigenvalues",
            "course_id": 1,
            "cutoff_year": cutoff,
        },
    )
    assert res.status_code == 200
    data = res.json()

    if data["provenance"] == "HISTORICAL_EVIDENCE":
        for q in data["questions"]:
            assert q["exam_year"] < cutoff, f"Question leaked from year {q['exam_year']} >= cutoff {cutoff}"


def test_mintai_course_isolation(prod_client: TestClient):
    """Verify questions generated for Course 1 do not leak into Course 2."""
    res1 = prod_client.post(
        "/api/intelligence/generate-questions",
        json={"topic": "Eigenvalues", "course_id": 1},
    )
    res2 = prod_client.post(
        "/api/intelligence/generate-questions",
        json={"topic": "Eigenvalues", "course_id": 2},  # Chemistry
    )
    assert res1.status_code == 200
    assert res2.status_code == 200

    # Calculus has historical questions for Eigenvalues
    data1 = res1.json()
    assert data1["course_id"] == 1
    assert data1["provenance"] == "HISTORICAL_EVIDENCE"
    assert data1["is_synthetic"] is False

    # Chemistry has no 'Eigenvalues' historical questions, so it must fall back to synthetic
    data2 = res2.json()
    assert data2["course_id"] == 2
    assert data2["provenance"] == "SYNTHETIC_SYLLABUS_FALLBACK"
    assert data2["is_synthetic"] is True
