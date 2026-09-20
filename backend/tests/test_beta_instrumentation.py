import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import SessionLocal, engine, Base
from backend.models.beta_telemetry import BetaEvent, BetaFeedback, BetaError

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_beta_tables():
    Base.metadata.create_all(bind=engine, tables=[
        BetaEvent.__table__,
        BetaFeedback.__table__,
        BetaError.__table__
    ])
    db = SessionLocal()
    try:
        db.query(BetaEvent).delete()
        db.query(BetaFeedback).delete()
        db.query(BetaError).delete()
        db.commit()
    finally:
        db.close()
    yield
    db = SessionLocal()
    try:
        db.query(BetaEvent).delete()
        db.query(BetaFeedback).delete()
        db.query(BetaError).delete()
        db.commit()
    finally:
        db.close()


def test_record_beta_funnel_events():
    events_payload = {
        "events": [
            {
                "session_id": "anon_session_1",
                "event_name": "landing",
                "route": "/"
            },
            {
                "session_id": "anon_session_1",
                "event_name": "course_selection",
                "route": "/mintai",
                "course_id": 1,
                "course_code": "21MAB101T",
                "metadata": {"status": "MATCHED"}
            },
            {
                "session_id": "anon_session_1",
                "event_name": "assessment_selection",
                "route": "/mintai",
                "course_id": 1,
                "course_code": "21MAB101T",
                "assessment_cycle": "ENDSEM"
            },
            {
                "session_id": "anon_session_1",
                "event_name": "intelligence_view",
                "route": "/mintai",
                "course_id": 1,
                "course_code": "21MAB101T",
                "assessment_cycle": "ENDSEM",
                "metadata": {"predictions_count": 5}
            },
            {
                "session_id": "anon_session_1",
                "event_name": "prediction_opened",
                "route": "/mintai",
                "course_id": 1,
                "course_code": "21MAB101T",
                "metadata": {"topic": "Eigenvalues", "rank": 1}
            },
            {
                "session_id": "anon_session_1",
                "event_name": "why_opened",
                "route": "/mintai",
                "course_id": 1,
                "course_code": "21MAB101T",
                "metadata": {"target_type": "topic", "topic_name": "Eigenvalues"}
            },
            {
                "session_id": "anon_session_1",
                "event_name": "practice_started",
                "route": "/mintai",
                "course_id": 1,
                "course_code": "21MAB101T"
            },
            {
                "session_id": "anon_session_1",
                "event_name": "question_opened",
                "route": "/mintai",
                "course_id": 1,
                "course_code": "21MAB101T",
                "metadata": {"question_number": "14a"}
            },
            {
                "session_id": "anon_session_1",
                "event_name": "study_plan_opened",
                "route": "/mintai",
                "course_id": 1,
                "course_code": "21MAB101T"
            }
        ]
    }

    resp = client.post("/api/analytics/events", json=events_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["recorded"] == 9

    db = SessionLocal()
    try:
        events = db.query(BetaEvent).filter_by(session_id="anon_session_1").all()
        assert len(events) == 9
        event_names = [e.event_name for e in events]
        assert "landing" in event_names
        assert "course_selection" in event_names
        assert "why_opened" in event_names
        assert "practice_started" in event_names
    finally:
        db.close()


def test_friction_events_sanitization():
    # Attempt sending sensitive details in friction event
    friction_payload = {
        "events": [
            {
                "session_id": "anon_session_2",
                "event_name": "api_error",
                "route": "/mintai",
                "metadata": {
                    "token": "secret_bearer_token_xyz",
                    "email": "student@srmist.edu.in",
                    "original_text": "Solve the quadratic equation x^2 + 2x + 1 = 0",
                    "safe_code": "HTTP_500"
                }
            },
            {
                "session_id": "anon_session_2",
                "event_name": "practice_empty",
                "route": "/mintai",
                "course_code": "21CYB101J"
            }
        ]
    }

    resp = client.post("/api/analytics/events", json=friction_payload)
    assert resp.status_code == 200

    db = SessionLocal()
    try:
        evt = db.query(BetaEvent).filter_by(session_id="anon_session_2", event_name="api_error").first()
        assert evt is not None
        meta = evt.metadata_json or {}
        # Blocked sensitive keys must be completely removed
        assert "token" not in meta
        assert "email" not in meta
        assert "original_text" not in meta
        # Safe non-sensitive keys preserved
        assert meta.get("safe_code") == "HTTP_500"
    finally:
        db.close()


def test_beta_feedback_flow():
    # 1. Positive Feedback
    resp1 = client.post("/api/analytics/feedback", json={
        "session_id": "anon_session_3",
        "useful": True,
        "course_code": "21MAB101T",
        "route": "/mintai"
    })
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "ok"

    # 2. Constructive Feedback with reason (and test email redaction in text)
    resp2 = client.post("/api/analytics/feedback", json={
        "session_id": "anon_session_4",
        "useful": False,
        "confusion_reason": "Unit 3 topics were unexpected. Contact me at student123@srmist.edu.in",
        "course_code": "21CSC201J",
        "route": "/mintai"
    })
    assert resp2.status_code == 200

    db = SessionLocal()
    try:
        fb1 = db.query(BetaFeedback).filter_by(session_id="anon_session_3").first()
        assert fb1 is not None
        assert fb1.useful is True

        fb2 = db.query(BetaFeedback).filter_by(session_id="anon_session_4").first()
        assert fb2 is not None
        assert fb2.useful is False
        assert "[REDACTED_EMAIL]" in fb2.confusion_reason
        assert "student123@srmist.edu.in" not in fb2.confusion_reason
    finally:
        db.close()


def test_error_observability_endpoint():
    resp = client.post("/api/analytics/errors", json={
        "session_id": "anon_session_5",
        "route": "/mintai",
        "error_type": "UnhandledPromiseRejection",
        "message": "Failed to fetch credentials from auth bearer token secret123",
        "context": {
            "status": 500,
            "browser": "Chrome/120"
        }
    })
    assert resp.status_code == 200

    db = SessionLocal()
    try:
        err = db.query(BetaError).filter_by(session_id="anon_session_5").first()
        assert err is not None
        assert err.error_type == "UnhandledPromiseRejection"
        assert "[REDACTED_AUTH]" in err.message
        assert "secret123" not in err.message
        assert err.context_json["status"] == 500
    finally:
        db.close()


def test_beta_success_metrics_computation():
    # Seed 3 distinct student sessions:
    # Session A: completes full funnel through practice
    # Session B: reaches intelligence only
    # Session C: reaches course_selection only
    client.post("/api/analytics/events", json={
        "events": [
            {"session_id": "sA", "event_name": "landing"},
            {"session_id": "sA", "event_name": "course_selection", "course_code": "21MAB101T"},
            {"session_id": "sA", "event_name": "assessment_selection", "assessment_cycle": "ENDSEM"},
            {"session_id": "sA", "event_name": "intelligence_view", "course_code": "21MAB101T"},
            {"session_id": "sA", "event_name": "prediction_opened", "metadata": {"rank": 1}},
            {"session_id": "sA", "event_name": "why_opened", "metadata": {"topic": "Matrices"}},
            {"session_id": "sA", "event_name": "study_plan_opened"},
            {"session_id": "sA", "event_name": "practice_started"},
            
            {"session_id": "sB", "event_name": "landing"},
            {"session_id": "sB", "event_name": "course_selection", "course_code": "21CYB101J"},
            {"session_id": "sB", "event_name": "intelligence_view", "course_code": "21CYB101J"},

            {"session_id": "sC", "event_name": "landing"},
            {"session_id": "sC", "event_name": "course_selection", "course_code": "21EEB101J"}
        ]
    })

    # Add 1 feedback
    client.post("/api/analytics/feedback", json={
        "session_id": "sA",
        "useful": True,
        "course_code": "21MAB101T"
    })

    resp = client.get("/api/analytics/beta-metrics")
    assert resp.status_code == 200
    metrics = resp.json()

    assert metrics["total_beta_sessions"] == 3
    funnel = metrics["funnel_sessions"]
    assert funnel["landing"] == 3
    assert funnel["course_selection"] == 3
    assert funnel["intelligence_view"] == 2
    assert funnel["practice_started"] == 1
    assert funnel["why_opened"] == 1
    assert funnel["study_plan_opened"] == 1

    conversions = metrics["conversion_rates"]
    # course (3) -> intelligence (2): 2/3 = 0.6667
    assert conversions["course_to_intelligence"] == 0.6667
    # intelligence (2) -> practice (1): 1/2 = 0.5
    assert conversions["intelligence_to_practice"] == 0.5
    # why interaction rate: 1/2 = 0.5
    assert conversions["why_interaction_rate"] == 0.5
    # study plan usage rate: 1/2 = 0.5
    assert conversions["study_plan_usage_rate"] == 0.5

    feedback = metrics["feedback_summary"]
    assert feedback["total_feedback"] == 1
    assert feedback["useful_count"] == 1
    assert feedback["useful_percentage"] == 100.0
