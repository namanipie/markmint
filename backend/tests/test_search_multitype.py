import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_search_course_by_code_and_name():
    res = client.post("/api/search/", json={"raw_query": "Calculus", "limit": 5})
    assert res.status_code == 200
    results = res.json()
    assert len(results) > 0
    # Should find course or topic
    types = [r["result_type"] for r in results]
    assert any(t in {"course", "topic", "concept", "exam_question"} for t in types)


def test_search_question_intent():
    res = client.post("/api/search/", json={"raw_query": "matrix question", "limit": 5})
    assert res.status_code == 200
    results = res.json()
    assert len(results) > 0
    assert results[0]["result_type"] == "exam_question"
