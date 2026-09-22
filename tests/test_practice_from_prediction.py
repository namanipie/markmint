import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.core.database import Base, get_db
from backend.models.core import (
    Course, CourseTrack, Exam, Section, Question,
    QuestionFamily, QuestionFamilyMembership, Unit, Topic, Syllabus
)


@pytest.fixture(scope="module")
def practice_test_setup():
    """Create an isolated in-memory SQLite database populated with multi-course, multi-track, and multi-cycle exam data."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()

    # 1. Course 1: Mathematics (Single track)
    course_math = Course(name="Mathematics", code="MATH101", canonical_code="21MAB101T")
    # 2. Course 2: Physics (Another course to test cross-course isolation)
    course_phys = Course(name="Physics", code="PHYS101", canonical_code="21PYB101T")
    # 3. Course 3: Foreign Languages (Multi-track)
    course_lang = Course(name="Foreign Languages", code="LANG101", canonical_code="21FLB101T")
    db.add_all([course_math, course_phys, course_lang])
    db.commit()

    # Language Tracks for Course 3
    track_german = CourseTrack(course_id=course_lang.id, track_key="german", track_name="German", track_code="GER101")
    track_french = CourseTrack(course_id=course_lang.id, track_key="french", track_name="French", track_code="FRE101")
    db.add_all([track_german, track_french])
    db.commit()

    # Syllabus and Topics for Mathematics
    syl_math = Syllabus(course_id=course_math.id, version="2021")
    db.add(syl_math)
    db.commit()
    unit_math = Unit(syllabus_id=syl_math.id, number=1, name="Linear Algebra")
    db.add(unit_math)
    db.commit()
    topic_matrices = Topic(unit_id=unit_math.id, name="Matrix Operations")
    topic_eigen = Topic(unit_id=unit_math.id, name="Eigenvalues and Eigenvectors")
    db.add_all([topic_matrices, topic_eigen])
    db.commit()

    # Question Families
    fam_eigen = QuestionFamily(
        subject="Mathematics",
        canonical_name="Cayley-Hamilton Theorem Eigenvalues",
        description="Eigenvalue problems via Cayley-Hamilton",
        repetition_type="family_repeat",
        first_seen_year=2021,
        latest_seen_year=2023,
    )
    fam_german = QuestionFamily(
        subject="Foreign Languages",
        canonical_name="German Conjugation Patterns",
        description="Regular verb conjugation",
        repetition_type="exact_repeat",
        first_seen_year=2022,
        latest_seen_year=2023,
    )
    db.add_all([fam_eigen, fam_german])
    db.commit()

    # Exams for Math:
    # Exam 1: 2021 CT1
    exam_2021_ct1 = Exam(course_id=course_math.id, year=2021, assessment_type="CT1")
    # Exam 2: 2022 CT1
    exam_2022_ct1 = Exam(course_id=course_math.id, year=2022, assessment_type="CT1")
    # Exam 3: 2023 ENDSEM
    exam_2023_endsem = Exam(course_id=course_math.id, year=2023, assessment_type="ENDSEM")
    # Exam 4 for Physics (cross-course leak test): 2023 CT1
    exam_phys_2023 = Exam(course_id=course_phys.id, year=2023, assessment_type="CT1")

    # Exams for Foreign Languages:
    exam_german = Exam(course_id=course_lang.id, track_id=track_german.id, year=2023, assessment_type="ENDSEM")
    exam_french = Exam(course_id=course_lang.id, track_id=track_french.id, year=2023, assessment_type="ENDSEM")

    db.add_all([exam_2021_ct1, exam_2022_ct1, exam_2023_endsem, exam_phys_2023, exam_german, exam_french])
    db.commit()

    # Sections
    sec_2021 = Section(exam_id=exam_2021_ct1.id, name="Part A")
    sec_2022 = Section(exam_id=exam_2022_ct1.id, name="Part A")
    sec_2023 = Section(exam_id=exam_2023_endsem.id, name="Part B")
    sec_phys = Section(exam_id=exam_phys_2023.id, name="Part A")
    sec_ger = Section(exam_id=exam_german.id, name="Section A")
    sec_fre = Section(exam_id=exam_french.id, name="Section A")
    db.add_all([sec_2021, sec_2022, sec_2023, sec_phys, sec_ger, sec_fre])
    db.commit()

    # Questions for fam_eigen in Math:
    # Q1: 2021 CT1, 5 marks
    q1 = Question(
        section_id=sec_2021.id,
        family_id=fam_eigen.id,
        question_number="1a",
        original_text="Find the eigenvalues of matrix A",
        marks=5.0,
        difficulty=0.4,
        cognitive_level="APPLY",
        topics=[topic_eigen],
    )
    # Q2: 2022 CT1, 10 marks
    q2 = Question(
        section_id=sec_2022.id,
        family_id=fam_eigen.id,
        question_number="2b",
        original_text="Verify Cayley-Hamilton theorem for matrix B",
        marks=10.0,
        difficulty=0.7,
        cognitive_level="ANALYZE",
        topics=[topic_eigen, topic_matrices],
    )
    # Q3: 2023 ENDSEM, 15 marks
    q3 = Question(
        section_id=sec_2023.id,
        family_id=fam_eigen.id,
        question_number="3c",
        original_text="Find the characteristic equation and eigenvalues of matrix C",
        marks=15.0,
        difficulty=0.8,
        cognitive_level="EVALUATE",
        topics=[topic_eigen],
    )

    # Cross-course Question: In Physics, linked to fam_eigen (simulated accidental linkage)
    q_phys = Question(
        section_id=sec_phys.id,
        family_id=fam_eigen.id,
        question_number="P1",
        original_text="Physics question erroneously tagged with math family",
        marks=5.0,
    )

    # Questions for German vs French in fam_german
    q_ger = Question(
        section_id=sec_ger.id,
        family_id=fam_german.id,
        question_number="G1",
        original_text="Konjugieren Sie das Verb 'haben'",
        marks=2.0,
    )
    q_fre = Question(
        section_id=sec_fre.id,
        family_id=fam_german.id,
        question_number="F1",
        original_text="Conjuguez le verbe 'avoir'",
        marks=2.0,
    )

    db.add_all([q1, q2, q3, q_phys, q_ger, q_fre])
    db.commit()

    def override_get_db():
        try:
            db_session = TestingSessionLocal()
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield {
        "course_math": course_math,
        "course_phys": course_phys,
        "course_lang": course_lang,
        "fam_eigen": fam_eigen,
        "fam_german": fam_german,
        "q1": q1,
        "q2": q2,
        "q3": q3,
    }

    app.dependency_overrides.clear()


@pytest.fixture
def client(practice_test_setup):
    with TestClient(app) as c:
        yield c


def test_valid_family_retrieval(client, practice_test_setup):
    """1. Valid Question Family returns verified historical questions with correct schema."""
    fam_id = practice_test_setup["fam_eigen"].id
    resp = client.get(f"/api/practice/from-prediction/{fam_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["family_id"] == fam_id
    assert data["family_name"] == "Cayley-Hamilton Theorem Eigenvalues"
    assert data["repetition_type"] == "family_repeat"
    assert data["assessment_cycle"] == "ALL"
    assert data["canonical_topic"] == "Eigenvalues and Eigenvectors"
    assert len(data["questions"]) >= 3

    # Check question fields
    first_q = data["questions"][0]
    assert "id" in first_q
    assert "question_number" in first_q
    assert "text" in first_q
    assert "marks" in first_q
    assert "year" in first_q
    assert "difficulty" in first_q
    assert "cognitive_level" in first_q


def test_nonexistent_family_returns_404(client):
    """2. Nonexistent Question Family returns 404."""
    resp = client.get("/api/practice/from-prediction/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Question family not found"


def test_nonexistent_course_returns_404(client, practice_test_setup):
    """3. Nonexistent course_id returns 404."""
    fam_id = practice_test_setup["fam_eigen"].id
    resp = client.get(f"/api/practice/from-prediction/{fam_id}?course_id=INVALID_COURSE")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Course not found"


def test_course_isolation_prevents_leakage(client, practice_test_setup):
    """4. Supplying course_id strictly isolates questions to that course, preventing cross-course leakage."""
    fam_id = practice_test_setup["fam_eigen"].id
    course_math_id = practice_test_setup["course_math"].id

    resp = client.get(f"/api/practice/from-prediction/{fam_id}?course_id={course_math_id}")
    assert resp.status_code == 200
    data = resp.json()

    # All returned questions must be from Math, not Physics
    assert data["course_id"] == course_math_id
    assert data["course_name"] == "Mathematics"
    for q in data["questions"]:
        assert "Physics" not in q["text"]


def test_language_track_isolation(client, practice_test_setup):
    """5. Language track filtering isolates questions by track in multi-track courses."""
    fam_id = practice_test_setup["fam_german"].id
    course_lang_id = practice_test_setup["course_lang"].id

    # Filter for German track
    resp_ger = client.get(
        f"/api/practice/from-prediction/{fam_id}?course_id={course_lang_id}&language=german"
    )
    assert resp_ger.status_code == 200
    data_ger = resp_ger.json()
    assert len(data_ger["questions"]) == 1
    assert "Konjugieren" in data_ger["questions"][0]["text"]
    assert "Conjuguez" not in data_ger["questions"][0]["text"]

    # Filter for French track
    resp_fre = client.get(
        f"/api/practice/from-prediction/{fam_id}?course_id={course_lang_id}&language=french"
    )
    assert resp_fre.status_code == 200
    data_fre = resp_fre.json()
    assert len(data_fre["questions"]) == 1
    assert "Conjuguez" in data_fre["questions"][0]["text"]

    # Invalid language track returns 400
    resp_inv = client.get(
        f"/api/practice/from-prediction/{fam_id}?course_id={course_lang_id}&language=japanese"
    )
    assert resp_inv.status_code == 400
    assert "Invalid language track" in resp_inv.json()["detail"]


def test_assessment_cycle_filtering(client, practice_test_setup):
    """6. Assessment cycle filtering normalizes input and returns only cycle-matching questions."""
    fam_id = practice_test_setup["fam_eigen"].id
    course_math_id = practice_test_setup["course_math"].id

    # Filter for CT1: should include 2021 CT1 (5 marks) and 2022 CT1 (10 marks), but NOT 2023 ENDSEM (15 marks)
    resp = client.get(
        f"/api/practice/from-prediction/{fam_id}?course_id={course_math_id}&assessment_cycle=ct-1"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["assessment_cycle"] == "CT1"
    years = [q["year"] for q in data["questions"]]
    assert 2023 not in years
    assert 2022 in years
    assert 2021 in years


def test_deterministic_ordering(client, practice_test_setup):
    """7. Deterministic ordering: latest year first, then highest marks, then stable ID."""
    fam_id = practice_test_setup["fam_eigen"].id
    course_math_id = practice_test_setup["course_math"].id

    resp = client.get(f"/api/practice/from-prediction/{fam_id}?course_id={course_math_id}")
    assert resp.status_code == 200
    data = resp.json()

    # Expected order: 2023 (15 marks), 2022 (10 marks), 2021 (5 marks)
    questions = data["questions"]
    assert questions[0]["year"] == 2023
    assert questions[0]["marks"] == 15.0
    assert questions[1]["year"] == 2022
    assert questions[1]["marks"] == 10.0
    assert questions[2]["year"] == 2021
    assert questions[2]["marks"] == 5.0


def test_limit_parameter_respected(client, practice_test_setup):
    """8. The limit query parameter is strictly respected."""
    fam_id = practice_test_setup["fam_eigen"].id
    course_math_id = practice_test_setup["course_math"].id

    resp = client.get(f"/api/practice/from-prediction/{fam_id}?course_id={course_math_id}&limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["questions"]) == 2
    # Should be top 2 in deterministic order (2023 and 2022)
    assert data["questions"][0]["year"] == 2023
    assert data["questions"][1]["year"] == 2022


def test_canonical_topic_consensus(client, practice_test_setup):
    """9. Canonical topic resolves to the consensus topic across member questions."""
    fam_id = practice_test_setup["fam_eigen"].id
    course_math_id = practice_test_setup["course_math"].id

    resp = client.get(f"/api/practice/from-prediction/{fam_id}?course_id={course_math_id}")
    assert resp.status_code == 200
    data = resp.json()
    # Eigenvalues appears in Q1, Q2, Q3 (3 times), Matrices only in Q2 (1 time)
    assert data["canonical_topic"] == "Eigenvalues and Eigenvectors"
