"""
Integration tests for Chemistry intelligence snapshot API endpoint.
Verifies topic mode resolution, taxonomy counts, predictions payload, and family evidence preservation.
"""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_chemistry_intelligence_snapshot_reports_topic_mode() -> None:
    """Verifies that Chemistry (Course 2) snapshot resolves to 'topic' mode with topic predictions."""
    res = client.get("/api/intelligence/2")
    assert res.status_code == 200
    data = res.json()

    assert data["data_availability_status"] == "READY"
    assert data["course"]["id"] == 2
    assert data["course"]["canonical_code"] == "21CYB101J"

    # Taxonomy & Mode semantics
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 45
    assert data["topic_predictions_count"] > 0
    assert data["prediction_mode"] == "topic"

    # Topic predictions payload
    preds = data["predictions"]
    assert len(preds) > 0
    assert preds[0]["category"] == "topic"
    assert "name" in preds[0]
    assert "probability" in preds[0]
    assert "confidence" in preds[0]

    # Family predictions preserved as complementary layer
    assert data["family_predictions_count"] > 0
    assert "family_predictions" in data
    assert len(data["family_predictions"]) > 0


def test_calculus_intelligence_unaffected() -> None:
    """Verifies that Calculus (Course 1) snapshot remains invariant."""
    res = client.get("/api/intelligence/1")
    assert res.status_code == 200
    data = res.json()

    assert data["course"]["id"] == 1
    assert data["has_topic_taxonomy"] is True
    assert data["taxonomy_topic_count"] == 27
    assert data["prediction_mode"] == "topic"
    assert len(data["predictions"]) > 0


def test_multi_track_course_intelligence_semantics() -> None:
    """Verifies that multi-track Course 8 enforces track selection, and resolves topic mode when selected."""
    res = client.get("/api/intelligence/8")
    assert res.status_code == 400
    assert "TRACK_SELECTION_REQUIRED" in res.json()["detail"]

    res_track = client.get("/api/intelligence/8?language=german")
    assert res_track.status_code == 200
    data = res_track.json()
    assert data["course"]["id"] == 8
    assert data["has_topic_taxonomy"] is True
    assert data["prediction_mode"] == "topic"
    assert data["topic_predictions_count"] > 0
