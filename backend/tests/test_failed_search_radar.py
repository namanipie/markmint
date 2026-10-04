import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.core import FailedSearchLog


def test_valid_telemetry_persists(client: TestClient, db_session: Session):
    """Verify that a valid failed search telemetry payload is persisted to database."""
    unique_query = f"quantum_cryptography_{datetime.utcnow().timestamp()}"
    res = client.post(
        "/api/admin/radar/fail",
        json={"query": unique_query, "assessment": "CT-1", "subject": "Physics"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "logged"
    assert data["query"] == unique_query
    assert data["deduplicated"] is False

    # Verify DB persistence
    log = db_session.query(FailedSearchLog).filter(FailedSearchLog.query == unique_query).first()
    assert log is not None
    assert log.assessment == "CT-1"
    assert log.subject == "Physics"


def test_invalid_payload_rejected(client: TestClient):
    """Verify empty or whitespace-only query payloads are rejected with 422."""
    res1 = client.post("/api/admin/radar/fail", json={"query": ""})
    assert res1.status_code == 422

    res2 = client.post("/api/admin/radar/fail", json={"query": "   "})
    assert res2.status_code == 422

    res3 = client.post("/api/admin/radar/fail", json={})
    assert res3.status_code == 422


def test_malformed_and_control_characters_sanitized(client: TestClient, db_session: Session):
    """Verify control characters are stripped and queries safely sanitized."""
    malformed_query = "malicious\x00\x08test\x1fquery"
    res = client.post(
        "/api/admin/radar/fail",
        json={"query": malformed_query},
    )
    assert res.status_code == 200
    data = res.json()
    assert "\x00" not in data["query"]
    assert "\x08" not in data["query"]
    assert "\x1f" not in data["query"]
    assert data["query"] == "malicioustestquery"


def test_duplicate_repeated_failures_debounced(client: TestClient, db_session: Session):
    """Verify that identical repeated queries within debounce window are throttled without extra rows."""
    q_name = f"debounce_query_{datetime.utcnow().timestamp()}"
    
    # First submit
    res1 = client.post(
        "/api/admin/radar/fail",
        json={"query": q_name, "assessment": "ENDSEM"},
    )
    assert res1.status_code == 200
    assert res1.json()["deduplicated"] is False

    # Immediate second submit (same query & assessment)
    res2 = client.post(
        "/api/admin/radar/fail",
        json={"query": q_name, "assessment": "ENDSEM"},
    )
    assert res2.status_code == 200
    assert res2.json()["deduplicated"] is True

    # Check only 1 row in database for this query
    count = db_session.query(FailedSearchLog).filter(FailedSearchLog.query == q_name).count()
    assert count == 1


def test_unauthorized_access_to_radar_stats(client: TestClient):
    """Verify that unauthenticated access to radar stats is blocked with 401."""
    res = client.get("/api/admin/radar/stats")
    assert res.status_code == 401


def test_authorized_access_and_aggregation(client: TestClient, db_session: Session, monkeypatch):
    """Verify admin-authorized access and accurate stats aggregation."""
    from backend.core.config import settings
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "test-secret-moderation-key")

    # Seed known failures
    seed_q = f"aggregation_target_{datetime.utcnow().timestamp()}"
    db_session.add(FailedSearchLog(query=seed_q, assessment="CT-1", timestamp=datetime.utcnow()))
    db_session.add(FailedSearchLog(query=seed_q, assessment="CT-1", timestamp=datetime.utcnow()))
    db_session.add(FailedSearchLog(query=seed_q, assessment="CT-2", timestamp=datetime.utcnow()))
    db_session.commit()

    # Query stats with admin authorization
    res = client.get(
        "/api/admin/radar/stats?days=7",
        headers={"X-Admin-Key": "test-secret-moderation-key"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "total_fails" in data
    assert "priorities" in data
    assert "active_users_24h" in data
    assert data["time_range_days"] == 7

    # Find aggregated seed query
    item = next((p for p in data["priorities"] if p["query"] == seed_q and p["assessment"] == "CT-1"), None)
    assert item is not None
    assert item["count"] >= 2
    assert item["latest_occurrence"] is not None


def test_root_alias_paths(client: TestClient):
    """Verify that root alias path /admin/radar/fail functions properly."""
    res = client.post(
        "/admin/radar/fail",
        json={"query": f"root_alias_{datetime.utcnow().timestamp()}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "logged"
