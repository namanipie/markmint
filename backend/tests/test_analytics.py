"""
Automated test suite for MarkMint Repetition Analytics API.
Verifies endpoints:
- GET /api/analytics/{course_id}/overview
- GET /api/analytics/{course_id}/topics
- GET /api/analytics/{course_id}/families
- GET /api/analytics/{course_id}/questions/repeated
- GET /api/analytics/{course_id}/evolution
- GET /api/analytics/{course_id}/marks
"""
import pytest
from fastapi.testclient import TestClient


def test_analytics_overview_calculus(client: TestClient):
    resp = client.get("/api/analytics/1/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["course_id"] == 1
    assert "Calculus" in data["course_name"]
    assert data["total_papers"] == 13
    assert data["total_questions"] == 62
    assert isinstance(data["years"], list)
    assert len(data["top_repeated_topics"]) > 0


def test_analytics_overview_chemistry(client: TestClient):
    resp = client.get("/api/analytics/2/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["course_id"] == 2
    assert "Chemistry" in data["course_name"]
    assert data["total_papers"] == 4
    assert data["total_questions"] == 197
    assert len(data["top_repeated_topics"]) > 0


def test_analytics_overview_404(client: TestClient):
    resp = client.get("/api/analytics/9999/overview")
    assert resp.status_code == 404


def test_analytics_topics_with_filtering(client: TestClient):
    # Unfiltered
    resp = client.get("/api/analytics/1/topics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_topics"] > 0
    assert data["topics_with_questions"] > 0

    topics = data["topics"]
    first_topic = topics[0]
    assert "topic_id" in first_topic
    assert "topic_name" in first_topic
    assert "paper_coverage" in first_topic
    assert "recurrence_status" in first_topic

    # Filtered by unit
    resp_unit = client.get("/api/analytics/1/topics?unit=1")
    assert resp_unit.status_code == 200
    unit_data = resp_unit.json()
    for t in unit_data["topics"]:
        assert t["unit_number"] == 1

    # Filtered by min_marks
    resp_marks = client.get("/api/analytics/1/topics?min_marks=10")
    assert resp_marks.status_code == 200
    marks_data = resp_marks.json()
    for t in marks_data["topics"]:
        assert t["total_marks"] >= 10.0


def test_analytics_families_explorer(client: TestClient):
    resp = client.get("/api/analytics/1/families")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_families_found" in data
    assert "families" in data
    if data["families"]:
        f = data["families"][0]
        assert "family_id" in f
        assert "canonical_name" in f
        assert "appearances_count" in f
        assert "appearances" in f
        assert isinstance(f["appearances"], list)


def test_analytics_repeated_questions_distinction(client: TestClient):
    resp = client.get("/api/analytics/1/questions/repeated")
    assert resp.status_code == 200
    data = resp.json()
    assert "exact_repeats_count" in data
    assert "family_repeats_count" in data
    assert "exact_repeats" in data
    assert "family_repeats" in data

    for r in data["exact_repeats"]:
        assert r["repetition_type"] == "EXACT_REPEAT"
        assert len(r["instances"]) >= 2

    for f in data["family_repeats"]:
        assert f["repetition_type"] == "FAMILY_REPEAT"
        assert len(f["variants"]) >= 2


def test_analytics_evolution_timeline(client: TestClient):
    resp = client.get("/api/analytics/1/evolution")
    assert resp.status_code == 200
    data = resp.json()
    assert "timeline_years" in data
    assert "timeline" in data
    if data["timeline"]:
        entry = data["timeline"][0]
        assert "year" in entry
        assert "paper_count" in entry
        assert "topics" in entry
        assert "active_topics" in entry


def test_analytics_marks_distribution(client: TestClient):
    resp = client.get("/api/analytics/1/marks")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_questions_analyzed" in data
    assert isinstance(data["common_marks"], list)


def test_analytics_assessment_comparison(client: TestClient):
    resp = client.get("/api/analytics/1/assessment-comparison")
    assert resp.status_code == 200
    data = resp.json()
    assert data["course_id"] == 1
    assert "assessment_types" in data
    assert "topics" in data
    assert len(data["topics"]) > 0
    first_t = data["topics"][0]
    assert "topic_name" in first_t
    assert "assessment_breakdown" in first_t
    assert "bias" in first_t


def test_analytics_topic_intelligence(client: TestClient):
    resp = client.get("/api/analytics/1/topics/1/intelligence?student_id=test_student")
    assert resp.status_code == 200
    data = resp.json()
    assert data["course_id"] == 1
    assert data["topic_id"] == 1
    assert "repetition_metrics" in data
    assert "forecast" in data
    assert "personalization" in data
    assert "past_questions" in data
    assert data["personalization"]["student_id"] == "test_student"
    assert "priority_score" in data["personalization"]
    assert "recommended_action" in data["personalization"]
