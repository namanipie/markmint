import pytest
from fastapi.testclient import TestClient


def test_mintai_fallback_for_unindexed_subject(client: TestClient):
    """Verify unindexed course/topic gracefully produces clearly labeled synthetic questions."""
    novel_topic = "Full Stack Microservices Architecture with Kubernetes"
    res = client.post(
        "/api/intelligence/generate-questions",
        json={
            "topic": novel_topic,
            "course_id": None,
        },
    )
    assert res.status_code == 200
    data = res.json()

    assert data["topic"] == novel_topic
    assert data["provenance"] == "SYNTHETIC_SYLLABUS_FALLBACK"
    assert data["is_synthetic"] is True
    assert data["evidence_count"] == 0
    assert data["disclaimer"] is not None
    assert "not represent verified past exam papers" in data["disclaimer"].lower()

    # Check question structure and types
    questions = data["questions"]
    assert len(questions) >= 3

    types = {q["type"] for q in questions}
    assert "MCQ" in types
    assert "SHORT" in types

    for q in questions:
        assert q["provenance"] == "SYNTHETIC_SYLLABUS_FALLBACK"
        assert q["is_synthetic"] is True
        assert q["exam_year"] is None, "Synthetic fallback must never fabricate an exam year"
        assert "Synthetic" in q["source_label"]


def test_mintai_fallback_mcq_has_options(client: TestClient):
    """Verify synthetic 1-mark MCQs contain options."""
    res = client.post(
        "/api/intelligence/generate-questions",
        json={"topic": "Graph Algorithms and Shortest Path"},
    )
    assert res.status_code == 200
    data = res.json()
    mcq = next((q for q in data["questions"] if q["type"] == "MCQ"), None)
    assert mcq is not None
    assert mcq["options"] is not None
    assert len(mcq["options"]) >= 4
