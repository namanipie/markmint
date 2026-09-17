"""
Integration tests for Chemistry study plan generation.
Verifies that topic predictions correctly feed into topic study plan mode
without creating synthetic student mastery or modifying underlying algorithms.
"""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_chemistry_study_plan_topic_mode() -> None:
    """Verifies that Chemistry study plan generates in 'topic' mode."""
    res = client.get("/api/study/plan/Chemistry")
    assert res.status_code == 200
    data = res.json()

    assert data["course"] == "Chemistry"
    assert data["plan_mode"] == "topic"
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 45
    assert data["topic_predictions_count"] > 0
    assert data["family_predictions_count"] > 0

    topics = data["topics"]
    assert len(topics) > 0

    top_target = topics[0]
    assert top_target.get("name") is not None or top_target.get("topic") is not None
    assert "priority" in top_target
    assert "prediction_score" in top_target
    assert top_target["prediction_score"] > 0


def test_study_plan_priorities_match_topics() -> None:
    """Verifies priorities and topics lists are in sync for Chemistry."""
    res = client.get("/api/study/plan/Chemistry")
    assert res.status_code == 200
    data = res.json()

    assert len(data["priorities"]) == len(data["topics"])
