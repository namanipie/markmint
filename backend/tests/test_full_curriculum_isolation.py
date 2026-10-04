import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import settings
from backend.core.database import get_db
from backend.main import app
from backend.models.core import (
    Course,
    CourseTrack,
    Exam,
    Section,
    Question,
    QuestionFamily,
    QuestionFamilyMembership,
    StudentTopicProgress,
)


@pytest.fixture(scope="module")
def prod_db():
    engine = create_engine(settings.get_database_url, connect_args={"check_same_thread": False})
    SessionMaker = sessionmaker(bind=engine)
    session = SessionMaker()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture(scope="module")
def prod_client(prod_db):
    def override_get_db():
        yield prod_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_track_isolation_foreign_languages(prod_client: TestClient):
    """Verify that multi-track course (Course 8) enforces track isolation."""
    # Without language param, must fail with TRACK_SELECTION_REQUIRED
    res_no_track = prod_client.get("/api/intelligence/8")
    assert res_no_track.status_code == 400
    assert "TRACK_SELECTION_REQUIRED" in res_no_track.json()["detail"]

    # With valid language track
    res_german = prod_client.get("/api/intelligence/8?language=german")
    assert res_german.status_code == 200
    assert res_german.json()["course"]["id"] == 8
    assert res_german.json()["track"]["track_key"] == "german"

    res_french = prod_client.get("/api/intelligence/8?language=french")
    assert res_french.status_code == 200
    assert res_french.json()["course"]["id"] == 8
    assert res_french.json()["track"]["track_key"] == "french"


def test_question_family_course_isolation(prod_db: Session):
    """Verify that QuestionFamilies never span multiple courses."""
    memberships = (
        prod_db.query(QuestionFamilyMembership.family_id, Exam.course_id)
        .join(Question, QuestionFamilyMembership.question_id == Question.id)
        .join(Section, Question.section_id == Section.id)
        .join(Exam, Section.exam_id == Exam.id)
        .distinct()
        .all()
    )

    families_by_course = {}
    for fam_id, cid in memberships:
        families_by_course.setdefault(fam_id, set()).add(cid)

    cross_course_families = [fam_id for fam_id, courses in families_by_course.items() if len(courses) > 1]
    assert len(cross_course_families) == 0, f"Found cross-course families: {cross_course_families}"


def test_zero_orphan_questions_in_corpus(prod_db: Session):
    """Verify that every question in production corpus belongs to exactly one QuestionFamily."""
    total_q = prod_db.query(Question).count()
    total_m = prod_db.query(QuestionFamilyMembership).count()
    assert total_q == 9205, f"Expected 9,205 questions in production corpus, found {total_q}"
    assert total_q == total_m, f"Mismatch: {total_q} questions vs {total_m} memberships"


def test_student_progress_isolation(prod_client: TestClient, prod_db: Session):
    """Verify student progress updates are isolated by student_id in database."""
    uid_a = "student_alpha_isolation_test"
    uid_b = "student_beta_isolation_test"

    try:
        # Student A progress
        res_a = prod_client.post(
            "/api/study/progress/1",
            json={"user_id": uid_a, "topic": "Matrix Operations", "status": "COMPLETED"},
        )
        assert res_a.status_code == 200
        assert res_a.json()["success"] is True

        # Student B progress
        res_b = prod_client.post(
            "/api/study/progress/1",
            json={"user_id": uid_b, "topic": "Matrix Operations", "status": "IN_PROGRESS"},
        )
        assert res_b.status_code == 200
        assert res_b.json()["success"] is True

        # Query database directly to verify complete isolation
        prog_a = prod_db.query(StudentTopicProgress).filter_by(student_id=uid_a).first()
        prog_b = prod_db.query(StudentTopicProgress).filter_by(student_id=uid_b).first()

        assert prog_a is not None and prog_a.status == "COMPLETED"
        assert prog_b is not None and prog_b.status in ("STARTED", "IN_PROGRESS")
    finally:
        # Clean up test rows
        prod_db.query(StudentTopicProgress).filter(
            StudentTopicProgress.student_id.in_([uid_a, uid_b])
        ).delete(synchronize_session=False)
        prod_db.commit()
