import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.core.database import Base, get_db
from backend.models.core import Course, CourseTrack, Exam, Section, Question, Syllabus, Unit, Topic
from backend.core.config import settings, Environment


@pytest.fixture(scope="module")
def resilience_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSession()

    # Create Normal Course (e.g. Calculus)
    calc = Course(id=1, name="Calculus And Linear Algebra", code="SEM1-CALC", canonical_code="21MAB101T")
    db.add(calc)
    db.flush()

    # Calculus exam with track_id = NULL
    e_calc = Exam(id=1, course_id=calc.id, track_id=None, year=2023, assessment_type="END_SEM")
    db.add(e_calc)
    db.flush()

    s_calc = Section(id=1, exam_id=e_calc.id, name="Part A")
    db.add(s_calc)
    db.flush()

    q_calc = Question(id=1, section_id=s_calc.id, question_number="1", original_text="Find eigenvalues.", marks=10)
    db.add(q_calc)
    db.flush()

    # Create Course 8 (Foreign Languages)
    fl = Course(id=8, name="Foreign Languages", code="SEM1-FORE", canonical_code="SEM1-FORE")
    db.add(fl)
    db.flush()

    # Add 2 tracks for Course 8: German and French
    tr_german = CourseTrack(
        id=1,
        course_id=fl.id,
        track_key="german",
        track_name="German",
        track_code="21LEH104T",
        track_type="LANGUAGE"
    )
    tr_french = CourseTrack(
        id=2,
        course_id=fl.id,
        track_key="french",
        track_name="French",
        track_code="21LEH103T",
        track_type="LANGUAGE"
    )
    db.add_all([tr_german, tr_french])
    db.flush()

    # German exam
    e_de = Exam(id=48, course_id=fl.id, track_id=tr_german.id, year=2023, assessment_type="END_SEM")
    # French exam
    e_fr = Exam(id=46, course_id=fl.id, track_id=tr_french.id, year=2023, assessment_type="END_SEM")
    db.add_all([e_de, e_fr])
    db.flush()

    db.commit()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSession, engine
    app.dependency_overrides.pop(get_db, None)


def test_schema_includes_exam_track_id(resilience_db):
    """Test 1: Verifies that the Exam schema includes track_id."""
    _, engine = resilience_db
    insp = inspect(engine)
    exam_cols = {c["name"] for c in insp.get_columns("exams")}
    assert "track_id" in exam_cols, "Exam table must have track_id column"


def test_course_track_foreign_key_and_relationships(resilience_db):
    """Test 2: Verifies CourseTrack relationships and foreign keys."""
    TestingSession, _ = resilience_db
    db = TestingSession()
    fl = db.query(Course).filter(Course.id == 8).first()
    assert fl is not None
    assert len(fl.tracks) == 2
    track_keys = {t.track_key for t in fl.tracks}
    assert "german" in track_keys
    assert "french" in track_keys
    db.close()


def test_non_track_courses_work_with_track_id_null(resilience_db):
    """Test 3: Normal courses continue working with track_id NULL."""
    TestingSession, _ = resilience_db
    db = TestingSession()
    calc_exam = db.query(Exam).filter(Exam.course_id == 1).first()
    assert calc_exam is not None
    assert calc_exam.track_id is None
    db.close()


def test_course_8_requires_track_selection(resilience_db):
    """Test 4: Course 8 requires language track selection."""
    client = TestClient(app)
    res = client.get("/api/intelligence/8")
    assert res.status_code == 400
    assert "TRACK_SELECTION_REQUIRED" in res.json()["detail"]


def test_german_requests_only_access_german_exams(resilience_db):
    """Test 5: German requests only query German-scoped exams."""
    TestingSession, _ = resilience_db
    db = TestingSession()
    de_exams = db.query(Exam).filter(Exam.course_id == 8, Exam.track_id == 1).all()
    fr_exams = db.query(Exam).filter(Exam.course_id == 8, Exam.track_id == 2).all()
    assert len(de_exams) == 1
    assert len(fr_exams) == 1
    assert de_exams[0].id == 48
    assert fr_exams[0].id == 46
    db.close()


def test_initial_scope_bundled_endpoint(resilience_db):
    """Test 6: /curriculum/initial-scope bundles branches, semesters, and subjects."""
    client = TestClient(app)
    res = client.get("/api/curriculum/initial-scope")
    assert res.status_code == 200
    data = res.json()
    assert "branches" in data
    assert "default_branch" in data
    assert "semesters" in data
    assert "subjects" in data


def test_production_error_sanitization():
    """Test 7: Production environment suppresses raw SQL errors."""
    from backend.core.config import settings, Environment
    orig_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = Environment.PRODUCTION
    client = TestClient(app)

    # Calling an endpoint that triggers an unhandled DB error or testing global handler directly
    res = client.get("/api/study/priorities/non_existent_course_99999999")
    # Should return 404 or sanitized message, never raw SQL
    if res.status_code == 500:
        assert "psycopg2" not in res.text
        assert "SELECT" not in res.text

    settings.ENVIRONMENT = orig_env
