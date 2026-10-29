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


def test_mintai_cycle_test_1_blueprint(client: TestClient):
    """Verify MintAI fallback generation conforms to SRMIST CT1 Blueprint (Units 1 & 2)."""
    res = client.post(
        "/api/intelligence/generate-questions",
        json={"topic": "Quantum Teleportation Logic", "cycle": "CT1"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_synthetic"] is True
    assert "CT1" in data["disclaimer"]
    assert "Units 1 & 2" in data["disclaimer"]

    questions = data["questions"]
    assert len(questions) == 4

    # Part A (2 Marks MCQ and Short)
    q1 = questions[0]
    assert q1["marks"] == "2 Marks"
    assert q1["type"] == "MCQ"
    assert "Units 1 & 2" in q1["source_label"]
    assert len(q1["options"]) == 4

    q2 = questions[1]
    assert q2["marks"] == "2 Marks"
    assert q2["type"] == "SHORT"

    # Part B (5 Marks Short Analytical)
    q3 = questions[2]
    assert q3["marks"] == "5 Marks"

    # Part C (12 Marks Comprehensive)
    q4 = questions[3]
    assert q4["marks"] == "12 Marks"
    assert q4["type"] == "LONG"


def test_mintai_cycle_test_2_blueprint(client: TestClient):
    """Verify MintAI fallback generation conforms to SRMIST CT2 Blueprint (Units 3 & 4)."""
    res = client.post(
        "/api/intelligence/generate-questions",
        json={"topic": "Quantum Error Correction Codes", "cycle": "CT2"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_synthetic"] is True
    assert "CT2" in data["disclaimer"]
    assert "Units 3 & 4" in data["disclaimer"]

    questions = data["questions"]
    assert any("Units 3 & 4" in q["source_label"] for q in questions)
    assert any(q["marks"] == "12 Marks" for q in questions)
