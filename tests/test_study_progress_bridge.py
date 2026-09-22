import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.core.database import Base, get_db
from backend.models.core import (
    Course, Exam, Section, Question, QuestionFamily,
    QuestionFamilyMembership, Unit, Topic, Syllabus,
    StudentTopicProgress, question_topic
)


@pytest.fixture(scope="module")
def bridge_test_setup():
    """Create isolated in-memory SQLite database with multi-course taxonomy, families, and questions."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()

    # 1. Course 1: Mathematics
    course_math = Course(name="Mathematics", code="MATH101", canonical_code="21MAB101T")
    # 2. Course 2: Physics
    course_phys = Course(name="Physics", code="PHYS101", canonical_code="21PYB101T")
    db.add_all([course_math, course_phys])
    db.commit()

    # Syllabus and Topics for Math
    syl_math = Syllabus(course_id=course_math.id, version="2021")
    db.add(syl_math)
    db.commit()

    unit1 = Unit(syllabus_id=syl_math.id, number=1, name="Linear Algebra")
    unit2 = Unit(syllabus_id=syl_math.id, number=2, name="Calculus")
    db.add_all([unit1, unit2])
    db.commit()

    topic_matrices = Topic(unit_id=unit1.id, name="Matrices")
    topic_eigen = Topic(unit_id=unit1.id, name="Eigenvalues")
    topic_taylor = Topic(unit_id=unit2.id, name="Taylor Series")
    db.add_all([topic_matrices, topic_eigen, topic_taylor])

    # Syllabus and Topics for Physics
    syl_phys = Syllabus(course_id=course_phys.id, version="2021")
    db.add(syl_phys)
    db.commit()
    unit_phys = Unit(syllabus_id=syl_phys.id, number=1, name="Mechanics")
    db.add(unit_phys)
    db.commit()
    topic_kinematics = Topic(unit_id=unit_phys.id, name="Kinematics")
    db.add(topic_kinematics)
    db.commit()

    # Question Families
    fam_math_eigen = QuestionFamily(
        subject="Mathematics",
        canonical_name="Eigenvalue Computation",
        repetition_type="family_repeat",
    )
    fam_math_multi = QuestionFamily(
        subject="Mathematics",
        canonical_name="Matrix Diagonalization",
        repetition_type="family_repeat",
    )
    fam_math_tie = QuestionFamily(
        subject="Mathematics",
        canonical_name="Balanced Multi Topic",
        repetition_type="exact_repeat",
    )
    fam_phys_motion = QuestionFamily(
        subject="Physics",
        canonical_name="Projectile Motion",
        repetition_type="family_repeat",
    )
    db.add_all([fam_math_eigen, fam_math_multi, fam_math_tie, fam_phys_motion])
    db.commit()

    # Exams and Sections
    exam_math = Exam(course_id=course_math.id, year=2023, assessment_type="ENDSEM")
    exam_phys = Exam(course_id=course_phys.id, year=2023, assessment_type="ENDSEM")
    db.add_all([exam_math, exam_phys])
    db.commit()

    sec_math = Section(exam_id=exam_math.id, name="Part A")
    sec_phys = Section(exam_id=exam_phys.id, name="Part A")
    db.add_all([sec_math, sec_phys])
    db.commit()

    # Questions for fam_math_eigen (Single consensus: Eigenvalues)
    q_eigen1 = Question(
        section_id=sec_math.id,
        family_id=fam_math_eigen.id,
        question_number="1",
        original_text="Find eigenvalues of matrix A",
        marks=5.0,
        topics=[topic_eigen],
    )
    q_eigen2 = Question(
        section_id=sec_math.id,
        family_id=fam_math_eigen.id,
        question_number="2",
        original_text="Find characteristic roots",
        marks=5.0,
        topics=[topic_eigen],
    )

    # Questions for fam_math_multi (Topic: Matrices x2, Eigenvalues x1 -> Mode is Matrices)
    q_multi1 = Question(
        section_id=sec_math.id,
        family_id=fam_math_multi.id,
        question_number="3",
        original_text="Diagonalize matrix M",
        marks=10.0,
        topics=[topic_matrices, topic_eigen],
    )
    q_multi2 = Question(
        section_id=sec_math.id,
        family_id=fam_math_multi.id,
        question_number="4",
        original_text="Invert matrix M",
        marks=5.0,
        topics=[topic_matrices],
    )

    # Questions for fam_math_tie (Topic: Eigenvalues x1, Matrices x1 -> Alphabetical tie-break: Eigenvalues)
    q_tie1 = Question(
        section_id=sec_math.id,
        family_id=fam_math_tie.id,
        question_number="5",
        original_text="Eigen problem",
        marks=5.0,
        topics=[topic_eigen],
    )
    q_tie2 = Question(
        section_id=sec_math.id,
        family_id=fam_math_tie.id,
        question_number="6",
        original_text="Matrix problem",
        marks=5.0,
        topics=[topic_matrices],
    )

    # Question for fam_phys_motion
    q_phys1 = Question(
        section_id=sec_phys.id,
        family_id=fam_phys_motion.id,
        question_number="P1",
        original_text="Calculate range of projectile",
        marks=10.0,
        topics=[topic_kinematics],
    )

    db.add_all([q_eigen1, q_eigen2, q_multi1, q_multi2, q_tie1, q_tie2, q_phys1])
    db.commit()

    def override_get_db():
        try:
            db_session = TestingSessionLocal()
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield {
        "TestingSessionLocal": TestingSessionLocal,
        "course_math": course_math,
        "course_phys": course_phys,
        "topic_matrices": topic_matrices,
        "topic_eigen": topic_eigen,
        "topic_taylor": topic_taylor,
        "topic_kinematics": topic_kinematics,
        "fam_math_eigen": fam_math_eigen,
        "fam_math_multi": fam_math_multi,
        "fam_math_tie": fam_math_tie,
        "fam_phys_motion": fam_phys_motion,
    }

    app.dependency_overrides.clear()


@pytest.fixture
def client(bridge_test_setup):
    with TestClient(app) as c:
        yield c


def test_normal_topic_progress_still_works(client, bridge_test_setup):
    """1. Normal topic progress works via topic_id and topic name."""
    course_id = bridge_test_setup["course_math"].id
    topic_id = bridge_test_setup["topic_taylor"].id

    # A. Via topic_id
    resp1 = client.post(
        f"/api/study/progress/{course_id}",
        json={"topic_id": topic_id, "status": "STARTED", "user_id": "student_alpha"}
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["success"] is True
    assert data1["status"] == "STARTED"
    assert data1["topic_id"] == topic_id

    # B. Via topic name and complete_topic action
    resp2 = client.post(
        f"/api/study/progress/{course_id}",
        json={"topic": "Taylor Series", "action": "complete_topic", "user_id": "student_alpha"}
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["success"] is True
    assert data2["status"] == "COMPLETED"


def test_family_originated_progress_resolves_correctly(client, bridge_test_setup):
    """2. Family-originated progress safely resolves to the canonical topic."""
    course_id = bridge_test_setup["course_math"].id
    fam_id = bridge_test_setup["fam_math_eigen"].id
    expected_topic_id = bridge_test_setup["topic_eigen"].id

    resp = client.post(
        f"/api/study/progress/{course_id}",
        json={
            "family_id": fam_id,
            "status": "STARTED",
            "practice_attempted": 1,
            "practice_accuracy": 0.75,
            "user_id": "student_beta"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["status"] == "STARTED"
    assert data["topic_id"] == expected_topic_id

    # Verify directly in DB
    db = bridge_test_setup["TestingSessionLocal"]()
    try:
        prog = db.query(StudentTopicProgress).filter_by(
            student_id="student_beta", topic_id=expected_topic_id
        ).first()
        assert prog is not None
        assert prog.status == "STARTED"
        assert prog.practice_attempted == 1
        assert prog.practice_correct == 1
    finally:
        db.close()


def test_invalid_family_returns_expected_error(client, bridge_test_setup):
    """3. Nonexistent Question Family returns 404."""
    course_id = bridge_test_setup["course_math"].id
    resp = client.post(
        f"/api/study/progress/{course_id}",
        json={"family_id": 999999, "status": "STARTED", "user_id": "student_gamma"}
    )
    assert resp.status_code == 404
    assert "Question family not found" in resp.json()["detail"]


def test_cross_course_family_cannot_update_another_course(client, bridge_test_setup):
    """4. Question family from Physics cannot update Mathematics progress."""
    course_math_id = bridge_test_setup["course_math"].id
    fam_phys_id = bridge_test_setup["fam_phys_motion"].id

    resp = client.post(
        f"/api/study/progress/{course_math_id}",
        json={"family_id": fam_phys_id, "status": "STARTED", "user_id": "student_delta"}
    )
    assert resp.status_code == 400
    assert "does not belong to course" in resp.json()["detail"]

    # Verify no progress was created
    db = bridge_test_setup["TestingSessionLocal"]()
    try:
        count = db.query(StudentTopicProgress).filter_by(student_id="student_delta").count()
        assert count == 0
    finally:
        db.close()


def test_multi_topic_family_behavior_is_deterministic(client, bridge_test_setup):
    """5. Multi-topic family behavior resolves deterministically via consensus and tie-breaking."""
    course_id = bridge_test_setup["course_math"].id
    db = bridge_test_setup["TestingSessionLocal"]()

    # A. Majority mode consensus: Matrices has 2 questions, Eigenvalues has 1 question
    fam_multi_id = bridge_test_setup["fam_math_multi"].id
    topic_matrices_id = bridge_test_setup["topic_matrices"].id

    resp1 = client.post(
        f"/api/study/progress/{course_id}",
        json={"family_id": fam_multi_id, "status": "STARTED", "user_id": "student_multi"}
    )
    assert resp1.status_code == 200
    assert resp1.json()["topic_id"] == topic_matrices_id

    # B. Tie-break: Eigenvalues (count=1) vs Matrices (count=1). Alphabetical order chooses 'Eigenvalues'
    fam_tie_id = bridge_test_setup["fam_math_tie"].id
    topic_eigen_id = bridge_test_setup["topic_eigen"].id

    resp2 = client.post(
        f"/api/study/progress/{course_id}",
        json={"family_id": fam_tie_id, "status": "STARTED", "user_id": "student_tie"}
    )
    assert resp2.status_code == 200
    assert resp2.json()["topic_id"] == topic_eigen_id
    db.close()


def test_accuracy_updates_correctly(client, bridge_test_setup):
    """6. Practice accuracy and attempts increment correctly across multiple submissions."""
    course_id = bridge_test_setup["course_math"].id
    fam_id = bridge_test_setup["fam_math_eigen"].id
    topic_id = bridge_test_setup["topic_eigen"].id
    user_id = "student_acc_tester"

    # Attempt 1: 1 question, accuracy 0.8 (correct)
    resp1 = client.post(
        f"/api/study/progress/{course_id}",
        json={
            "family_id": fam_id,
            "practice_attempted": 1,
            "practice_accuracy": 0.8,
            "user_id": user_id
        }
    )
    assert resp1.status_code == 200

    db = bridge_test_setup["TestingSessionLocal"]()
    prog1 = db.query(StudentTopicProgress).filter_by(student_id=user_id, topic_id=topic_id).first()
    assert prog1.practice_attempted == 1
    assert prog1.practice_correct == 1
    db.close()

    # Attempt 2: 1 question, accuracy 0.3 (incorrect)
    resp2 = client.post(
        f"/api/study/progress/{course_id}",
        json={
            "family_id": fam_id,
            "practice_attempted": 1,
            "practice_accuracy": 0.3,
            "user_id": user_id
        }
    )
    assert resp2.status_code == 200

    db = bridge_test_setup["TestingSessionLocal"]()
    prog2 = db.query(StudentTopicProgress).filter_by(student_id=user_id, topic_id=topic_id).first()
    assert prog2.practice_attempted == 2
    assert prog2.practice_correct == 1
    db.close()

    # Attempt 3: 4 questions batch, accuracy 0.75 (3 correct)
    resp3 = client.post(
        f"/api/study/progress/{course_id}",
        json={
            "family_id": fam_id,
            "practice_attempted": 4,
            "practice_accuracy": 0.75,
            "user_id": user_id
        }
    )
    assert resp3.status_code == 200

    db = bridge_test_setup["TestingSessionLocal"]()
    prog3 = db.query(StudentTopicProgress).filter_by(student_id=user_id, topic_id=topic_id).first()
    assert prog3.practice_attempted == 6
    assert prog3.practice_correct == 4  # 1 + 3
    db.close()


def test_status_transitions_and_aliases(client, bridge_test_setup):
    """7. Status transitions remain valid; IN_PROGRESS is accepted as compatibility alias."""
    course_id = bridge_test_setup["course_math"].id
    topic_id = bridge_test_setup["topic_taylor"].id
    user_id = "student_transitions"

    # A. Alias IN_PROGRESS -> maps to STARTED
    resp1 = client.post(
        f"/api/study/progress/{course_id}",
        json={"topic_id": topic_id, "status": "IN_PROGRESS", "user_id": user_id}
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "STARTED"

    # B. Transition to COMPLETED
    resp2 = client.post(
        f"/api/study/progress/{course_id}",
        json={"topic_id": topic_id, "status": "COMPLETED", "user_id": user_id}
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "COMPLETED"

    # C. Reset to NOT_STARTED
    resp3 = client.post(
        f"/api/study/progress/{course_id}",
        json={"topic_id": topic_id, "action": "reset_topic", "user_id": user_id}
    )
    assert resp3.status_code == 200
    assert resp3.json()["status"] == "NOT_STARTED"

    # D. Invalid status is rejected with 400
    resp4 = client.post(
        f"/api/study/progress/{course_id}",
        json={"topic_id": topic_id, "status": "INVALID_STATE", "user_id": user_id}
    )
    assert resp4.status_code == 400
    assert "status must be" in resp4.json()["detail"]
