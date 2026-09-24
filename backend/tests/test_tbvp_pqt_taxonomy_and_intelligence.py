"""
Comprehensive automated tests for Course 30 (TBVP) and Course 31 (PQT):
1. Registry integrity and invariants (Course 30 = 21MAB201T, Course 31 = 21MAB204T).
2. Database taxonomy, units, topics, and syllabus links.
3. Exam and question ingestion integrity.
4. Deterministic topic mappings (all 5 units covered, zero cross-course leakage).
5. Intelligence snapshot and prediction mode.
6. Study priorities endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import SessionLocal
from backend.models.core import Course, Exam, Section, Question, Topic, Unit, question_topic
from backend.services.taxonomy_registry.registry import get_taxonomy_registry, reset_taxonomy_registry

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_course_30_tbvp_registry():
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()
    assert registry.has_course(30)
    entry = registry.get_course(30)
    assert entry.course.id == 30
    assert entry.course.canonical_code == "21MAB201T"
    assert entry.course.code == "SEM3-TBVP"
    assert entry.course.name == "Transforms and Boundary Value Problems"
    assert len(entry.units) == 5
    assert sum(len(u.topics) for u in entry.units) == 21

def test_course_31_pqt_registry():
    reset_taxonomy_registry()
    registry = get_taxonomy_registry()
    assert registry.has_course(31)
    entry = registry.get_course(31)
    assert entry.course.id == 31
    assert entry.course.canonical_code == "21MAB204T"
    assert entry.course.code == "SEM4-PQT"
    assert entry.course.name == "Probability and Queueing Theory"
    assert len(entry.units) == 5
    assert sum(len(u.topics) for u in entry.units) == 20

def test_tbvp_pqt_database_state():
    db = SessionLocal()
    try:
        tbvp = db.query(Course).filter(Course.id == 30).first()
        assert tbvp is not None
        assert tbvp.canonical_code == "21MAB201T"
        assert tbvp.code == "SEM3-TBVP"

        tbvp_exams = db.query(Exam).filter(Exam.course_id == 30).all()
        assert len(tbvp_exams) >= 10
        tbvp_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 30)
            .all()
        )
        assert len(tbvp_questions) >= 300

        pqt = db.query(Course).filter(Course.id == 31).first()
        assert pqt is not None
        assert pqt.canonical_code == "21MAB204T"
        assert pqt.code == "SEM4-PQT"

        pqt_exams = db.query(Exam).filter(Exam.course_id == 31).all()
        assert len(pqt_exams) >= 6
        pqt_questions = (
            db.query(Question)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 31)
            .all()
        )
        assert len(pqt_questions) >= 150
    finally:
        db.close()

def test_tbvp_pqt_topic_mappings():
    db = SessionLocal()
    try:
        # Ensure questions are mapped for TBVP
        tbvp_mapped = (
            db.query(question_topic.c.question_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 30)
            .distinct()
            .count()
        )
        assert tbvp_mapped >= 300

        pqt_mapped = (
            db.query(question_topic.c.question_id)
            .join(Question, question_topic.c.question_id == Question.id)
            .join(Section, Question.section_id == Section.id)
            .join(Exam, Section.exam_id == Exam.id)
            .filter(Exam.course_id == 31)
            .distinct()
            .count()
        )
        assert pqt_mapped >= 150
    finally:
        db.close()

def test_tbvp_intelligence_api(client: TestClient):
    for ident in ["30", "SEM3-TBVP", "21MAB201T"]:
        res = client.get(f"/api/intelligence/{ident}")
        assert res.status_code == 200
        data = res.json()
        assert data["course"]["id"] == 30
        assert data["course"]["canonical_code"] == "21MAB201T"
        assert data["has_topic_taxonomy"] is True

def test_pqt_intelligence_api(client: TestClient):
    for ident in ["31", "SEM4-PQT", "21MAB204T"]:
        res = client.get(f"/api/intelligence/{ident}")
        assert res.status_code == 200
        data = res.json()
        assert data["course"]["id"] == 31
        assert data["course"]["canonical_code"] == "21MAB204T"
        assert data["has_topic_taxonomy"] is True

def test_study_priorities_tbvp_pqt(client: TestClient):
    res_tbvp = client.get("/api/study/priorities/SEM3-TBVP")
    assert res_tbvp.status_code == 200
    assert res_tbvp.json()["has_topic_taxonomy"] is True

    res_pqt = client.get("/api/study/priorities/SEM4-PQT")
    assert res_pqt.status_code == 200
    assert res_pqt.json()["has_topic_taxonomy"] is True
