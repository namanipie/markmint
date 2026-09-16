import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.core.database import Base
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, Syllabus
from backend.services.search.discovery import DiscoverySearchEngine
from backend.schemas import SearchQuery, SearchResultType

client = TestClient(app)


def test_search_course_by_code_and_name():
    res = client.post("/api/search/", json={"raw_query": "Calculus", "limit": 5})
    assert res.status_code == 200
    results = res.json()
    assert len(results) > 0
    types = [r["result_type"] for r in results]
    assert any(t in {"course", "topic", "concept", "exam_question"} for t in types)


def test_search_question_intent():
    res = client.post("/api/search/", json={"raw_query": "matrix question", "limit": 5})
    assert res.status_code == 200
    results = res.json()
    assert len(results) > 0
    assert results[0]["result_type"] == "exam_question"


@pytest.fixture
def search_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_empty_and_whitespace_search_queries(search_db):
    engine = DiscoverySearchEngine(search_db)

    # Empty string
    res_empty = engine.search(query=SearchQuery(raw_query=""))
    assert res_empty == []

    # Whitespace only
    res_ws = engine.search(query=SearchQuery(raw_query="     \t \n "))
    assert res_ws == []


def test_special_character_search_sanitization(search_db):
    engine = DiscoverySearchEngine(search_db)

    # Queries with punctuation, wildcards, SQL characters
    tricky_queries = [
        "%%%",
        "___",
        "'; DROP TABLE courses; --",
        "***???",
        "\\\\\\",
        "\"'\"'",
        "<script>alert(1)</script>",
    ]

    for q in tricky_queries:
        # Must execute cleanly without unhandled database exceptions
        results = engine.search(query=SearchQuery(raw_query=q))
        assert isinstance(results, list)


def test_exam_multi_entity_search(search_db):
    course = Course(name="Thermodynamics", code="ME201")
    search_db.add(course)
    search_db.commit()

    exam = Exam(
        course_id=course.id,
        year=2024,
        term="Odd Semester",
        assessment_type="END_SEM",
    )
    search_db.add(exam)
    search_db.commit()

    engine = DiscoverySearchEngine(search_db)

    # Search specifically for exams / papers
    results = engine.search(query=SearchQuery(raw_query="Thermodynamics END_SEM paper"))
    assert len(results) >= 1

    exam_results = [r for r in results if r.result_type == SearchResultType.EXAM]
    assert len(exam_results) >= 1
    found_exam = exam_results[0]
    assert "END_SEM" in found_exam.title
    assert found_exam.year == 2024
    assert found_exam.metadata["course_id"] == course.id


def test_real_world_search_queries():
    """
    Section 11: Real-World Search Queries
    Validates realistic searches:
    Calculus, 21MAB101T, quadratic forms, chemistry end sem, CT1, exam,
    question family, matrix, eigenvalues, empty, whitespace, symbols,
    very long query, mixed casing, multi-token, partial course code.
    """
    realistic_checks = [
        ("Calculus", 1, {"course", "topic", "exam", "question_family"}),
        ("21MAB101T", 1, {"course", "question_family"}),
        ("quadratic forms", 1, {"topic", "concept"}),
        ("chemistry end sem", 1, {"exam", "question_family"}),
        ("CT1", 1, {"exam"}),
        ("exam", 1, {"exam"}),
        ("question family", 1, {"question_family"}),
        ("matrix", 1, {"topic", "question_family", "exam_question"}),
        ("eigenvalues", 1, {"topic", "question_family", "concept"}),
        ("", 0, set()),
        ("    \t  ", 0, set()),
        ("!!!@@@###$$$%%%", 0, set()),
        ("A" * 500, 0, set()),
        ("cALCuLuS", 1, {"course", "topic", "exam"}),
        ("calculus quadratic", 1, {"topic", "question_family"}),
        ("21MAB", 1, {"course", "question_family"}),
    ]

    for q_str, min_count, expected_types in realistic_checks:
        res = client.post("/api/search/", json={"raw_query": q_str, "limit": 5})
        assert res.status_code == 200, f"Query '{q_str}' returned status {res.status_code}"
        items = res.json()
        assert len(items) >= min_count, f"Query '{q_str}' returned {len(items)} items, expected >= {min_count}"
        if expected_types:
            result_types = {item["result_type"] for item in items}
            assert result_types.intersection(expected_types), f"Query '{q_str}' types {result_types} missing expected {expected_types}"
        # Assert each item is valid SearchResult schema
        for item in items:
            assert "id" in item
            assert "result_type" in item
            assert "title" in item
            assert "relevance_score" in item

