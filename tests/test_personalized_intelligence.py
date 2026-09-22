import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.core.database import Base, get_db
from backend.models.core import (
    Course, Exam, Section, Question, QuestionFamily,
    Unit, Topic, Syllabus, StudentTopicProgress, question_topic
)
from backend.services.intelligence_cache import IntelligenceCacheService, build_cache_key


@pytest.fixture(scope="module")
def personalized_test_setup():
    """Create isolated in-memory SQLite database for testing personalized intelligence."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()

    # Course: Calculus
    course = Course(name="Calculus", code="CALC101", canonical_code="21MAB101T")
    db.add(course)
    db.commit()

    # Syllabus & Unit
    syllabus = Syllabus(course_id=course.id, version="2021")
    db.add(syllabus)
    db.commit()

    unit1 = Unit(syllabus_id=syllabus.id, number=1, name="Linear Algebra")
    unit2 = Unit(syllabus_id=syllabus.id, number=2, name="Differential Calculus")
    db.add_all([unit1, unit2])
    db.commit()

    topic_matrices = Topic(unit_id=unit1.id, name="Matrices")
    topic_eigen = Topic(unit_id=unit1.id, name="Eigenvalues")
    topic_limits = Topic(unit_id=unit2.id, name="Limits and Continuity")
    db.add_all([topic_matrices, topic_eigen, topic_limits])
    db.commit()

    # Question Families
    fam_eigen = QuestionFamily(
        subject="Calculus",
        canonical_name="Eigenvalue Problems",
        repetition_type="family_repeat",
    )
    fam_limits = QuestionFamily(
        subject="Calculus",
        canonical_name="LHopital Rule Limits",
        repetition_type="exact_repeat",
    )
    db.add_all([fam_eigen, fam_limits])
    db.commit()

    # Exams across 3 years
    exam2021 = Exam(course_id=course.id, year=2021, assessment_type="ENDSEM")
    exam2022 = Exam(course_id=course.id, year=2022, assessment_type="ENDSEM")
    exam2023 = Exam(course_id=course.id, year=2023, assessment_type="ENDSEM")
    db.add_all([exam2021, exam2022, exam2023])
    db.commit()

    sec2021 = Section(exam_id=exam2021.id, name="A")
    sec2022 = Section(exam_id=exam2022.id, name="A")
    sec2023 = Section(exam_id=exam2023.id, name="A")
    db.add_all([sec2021, sec2022, sec2023])
    db.commit()

    # Questions:
    # Eigenvalues appears in all 3 years (high probability)
    q1 = Question(section_id=sec2021.id, family_id=fam_eigen.id, question_number="1", original_text="Find eigenvalues of matrix A", marks=10.0, topics=[topic_eigen])
    q2 = Question(section_id=sec2022.id, family_id=fam_eigen.id, question_number="2", original_text="Find eigenvalues of matrix B", marks=10.0, topics=[topic_eigen])
    q3 = Question(section_id=sec2023.id, family_id=fam_eigen.id, question_number="3", original_text="Find eigenvalues of matrix C", marks=15.0, topics=[topic_eigen])

    # Limits appears in 2 years
    q4 = Question(section_id=sec2022.id, family_id=fam_limits.id, question_number="4", original_text="Compute limit using LHopital", marks=5.0, topics=[topic_limits])
    q5 = Question(section_id=sec2023.id, family_id=fam_limits.id, question_number="5", original_text="Evaluate limit as x approaches 0", marks=5.0, topics=[topic_limits])

    # Matrices appears in 1 year
    q6 = Question(section_id=sec2021.id, question_number="6", original_text="Compute matrix rank", marks=5.0, topics=[topic_matrices])

    db.add_all([q1, q2, q3, q4, q5, q6])
    db.commit()

    # Course 2: Family-only course (no syllabus taxonomy to test family-mode predictions)
    course_fam_only = Course(name="Special Topics", code="SPEC101", canonical_code="21SPB101T")
    db.add(course_fam_only)
    db.commit()

    exam_fam1 = Exam(course_id=course_fam_only.id, year=2022, assessment_type="ENDSEM")
    exam_fam2 = Exam(course_id=course_fam_only.id, year=2023, assessment_type="ENDSEM")
    db.add_all([exam_fam1, exam_fam2])
    db.commit()

    sec_fam1 = Section(exam_id=exam_fam1.id, name="A")
    sec_fam2 = Section(exam_id=exam_fam2.id, name="A")
    db.add_all([sec_fam1, sec_fam2])
    db.commit()

    fam_special = QuestionFamily(
        subject="Special Topics",
        canonical_name="Quantum Logic Gates",
        repetition_type="family_repeat",
    )
    db.add(fam_special)
    db.commit()

    q_sp1 = Question(section_id=sec_fam1.id, family_id=fam_special.id, question_number="1", original_text="Hadamard gate matrix", marks=10.0)
    q_sp2 = Question(section_id=sec_fam2.id, family_id=fam_special.id, question_number="2", original_text="Pauli-X gate matrix", marks=10.0)
    db.add_all([q_sp1, q_sp2])
    db.commit()

    # Clear memory cache before starting tests
    IntelligenceCacheService.clear_memory_cache()

    def override_get_db():
        try:
            db_session = TestingSessionLocal()
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield {
        "TestingSessionLocal": TestingSessionLocal,
        "course": course,
        "course_fam_only": course_fam_only,
        "topic_eigen": topic_eigen,
        "topic_limits": topic_limits,
        "topic_matrices": topic_matrices,
        "fam_eigen": fam_eigen,
        "fam_special": fam_special,
    }

    app.dependency_overrides.clear()
    IntelligenceCacheService.clear_memory_cache()


@pytest.fixture
def client(personalized_test_setup):
    with TestClient(app) as c:
        yield c


def test_historical_prediction_score_stays_identical_after_practice(client, personalized_test_setup):
    """A. Historical prediction score remains identical before and after student practice."""
    course_id = personalized_test_setup["course"].id
    topic_id = personalized_test_setup["topic_eigen"].id

    # 1. Anonymous baseline snapshot
    resp_anon = client.get(f"/api/intelligence/{course_id}")
    assert resp_anon.status_code == 200
    data_anon = resp_anon.json()

    # Find Eigenvalues prediction score in predictions and priorities
    anon_pred = next(p for p in data_anon["predictions"] if p["name"] == "Eigenvalues")
    baseline_score = anon_pred["score"]

    anon_priority = next(p for p in data_anon["study_priorities"] if p["name"] == "Eigenvalues")
    baseline_priority_score = anon_priority["prediction_score"]
    assert baseline_score == baseline_priority_score

    # 2. Student records mastery
    resp_prog = client.post(
        f"/api/study/progress/{course_id}",
        json={
            "topic_id": topic_id,
            "status": "COMPLETED",
            "practice_attempted": 5,
            "practice_accuracy": 1.0,
            "user_id": "student_score_invariance"
        }
    )
    assert resp_prog.status_code == 200

    # 3. Student requests personalized snapshot
    resp_student = client.get(f"/api/intelligence/{course_id}?student_id=student_score_invariance")
    assert resp_student.status_code == 200
    data_student = resp_student.json()

    # Historical prediction score MUST remain identical
    student_pred = next(p for p in data_student["predictions"] if p["name"] == "Eigenvalues")
    student_priority = next(p for p in data_student["study_priorities"] if p["name"] == "Eigenvalues")

    assert student_pred["score"] == baseline_score
    assert student_priority["prediction_score"] == baseline_priority_score


def test_completed_high_accuracy_topic_is_deprioritized(client, personalized_test_setup):
    """B & C. Completed high-accuracy topic is deprioritized from active study according to existing rules."""
    course_id = personalized_test_setup["course"].id
    topic_id = personalized_test_setup["topic_eigen"].id
    student_id = "student_deprioritize_test"

    # Before practice: unstudied topic priority
    resp_before = client.get(f"/api/intelligence/{course_id}?student_id={student_id}")
    priority_before = next(p for p in resp_before.json()["study_priorities"] if p["name"] == "Eigenvalues")
    assert priority_before["student_status"] == "NOT_STARTED"
    # Unstudied topic gets elevated to VERY_HIGH
    assert priority_before["priority"] in {"VERY_HIGH", "HIGH"}

    # Student completes topic with 100% accuracy
    client.post(
        f"/api/study/progress/{course_id}",
        json={
            "topic_id": topic_id,
            "status": "COMPLETED",
            "practice_attempted": 3,
            "practice_accuracy": 1.0,
            "user_id": student_id
        }
    )

    # After practice: personalized priority is deprioritized
    resp_after = client.get(f"/api/intelligence/{course_id}?student_id={student_id}")
    priority_after = next(p for p in resp_after.json()["study_priorities"] if p["name"] == "Eigenvalues")

    assert priority_after["student_status"] == "COMPLETED"
    assert priority_after["practice_accuracy"] == 1.0
    assert priority_after["recommended_action"] == "MAINTAIN_AND_REVIEW"
    assert any("deprioritized" in r.lower() for r in priority_after["reasons"])
    # Deprioritized: VERY_HIGH -> HIGH, or HIGH -> MEDIUM
    order = {"VERY_HIGH": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    assert order[priority_after["priority"]] > order[priority_before["priority"]]


def test_low_accuracy_or_unstudied_topic_is_elevated(client, personalized_test_setup):
    """D. Low-accuracy topic (< 60%) is elevated for urgent study."""
    course_id = personalized_test_setup["course"].id
    topic_id = personalized_test_setup["topic_eigen"].id
    student_id = "student_weak_tester"

    # Record weak performance (30% accuracy)
    client.post(
        f"/api/study/progress/{course_id}",
        json={
            "topic_id": topic_id,
            "status": "STARTED",
            "practice_attempted": 10,
            "practice_accuracy": 0.3,
            "user_id": student_id
        }
    )

    resp = client.get(f"/api/intelligence/{course_id}?student_id={student_id}")
    priority = next(p for p in resp.json()["study_priorities"] if p["name"] == "Eigenvalues")

    assert priority["student_status"] == "STARTED"
    assert any("below 60%" in r for r in priority["reasons"])
    assert priority["recommended_action"] in {"DEEP_STUDY_URGENT", "PRACTICE_QUESTIONS"}
    assert priority["priority"] in {"VERY_HIGH", "HIGH"}


def test_student_isolation_no_cross_contamination(client, personalized_test_setup):
    """E. Distinct students receive strictly their own progress without cross-contamination."""
    course_id = personalized_test_setup["course"].id
    topic_id = personalized_test_setup["topic_eigen"].id
    student_alice = "student_alice"
    student_bob = "student_bob"

    # Alice has mastered Eigenvalues
    client.post(
        f"/api/study/progress/{course_id}",
        json={"topic_id": topic_id, "status": "COMPLETED", "practice_attempted": 5, "practice_accuracy": 1.0, "user_id": student_alice}
    )

    # Bob has never touched it
    resp_alice = client.get(f"/api/intelligence/{course_id}?student_id={student_alice}").json()
    resp_bob = client.get(f"/api/intelligence/{course_id}?student_id={student_bob}").json()

    alice_eigen = next(p for p in resp_alice["study_priorities"] if p["name"] == "Eigenvalues")
    bob_eigen = next(p for p in resp_bob["study_priorities"] if p["name"] == "Eigenvalues")

    assert alice_eigen["student_status"] == "COMPLETED"
    assert alice_eigen["practice_accuracy"] == 1.0

    assert bob_eigen["student_status"] == "NOT_STARTED"
    assert bob_eigen["practice_accuracy"] is None


def test_anonymous_cached_snapshot_remains_safe(client, personalized_test_setup):
    """F. Anonymous cached snapshot remains safe and unpolluted by student progress."""
    course_id = personalized_test_setup["course"].id
    topic_id = personalized_test_setup["topic_eigen"].id
    student_id = "student_pollution_check"

    # 1. Warm anonymous cache
    resp1 = client.get(f"/api/intelligence/{course_id}")
    assert resp1.status_code == 200

    resp2 = client.get(f"/api/intelligence/{course_id}")
    assert resp2.status_code == 200
    assert resp2.json()["metadata"]["cache_hit"] is True

    # 2. Student completes topic
    client.post(
        f"/api/study/progress/{course_id}",
        json={"topic_id": topic_id, "status": "COMPLETED", "practice_attempted": 2, "practice_accuracy": 1.0, "user_id": student_id}
    )

    # 3. Anonymous snapshot must STILL be NOT_STARTED and served from cache
    resp_anon_again = client.get(f"/api/intelligence/{course_id}")
    assert resp_anon_again.status_code == 200
    assert resp_anon_again.json()["metadata"]["cache_hit"] is True

    anon_priority = next(p for p in resp_anon_again.json()["study_priorities"] if p["name"] == "Eigenvalues")
    assert anon_priority["student_status"] == "NOT_STARTED"
    assert anon_priority["practice_accuracy"] is None


def test_family_mode_predictions_reflect_topic_progress(client, personalized_test_setup):
    """G. Family-mode predictions do not hardcode NOT_STARTED when topic progress exists."""
    course_fam = personalized_test_setup["course_fam_only"]
    fam_special = personalized_test_setup["fam_special"]
    student_id = "student_family_mode_tester"

    # In course_fam_only, topic predictions is empty, so it falls back to family_predictions
    resp_baseline = client.get(f"/api/intelligence/{course_fam.id}?student_id={student_id}")
    assert resp_baseline.status_code == 200
    priorities = resp_baseline.json()["study_priorities"]
    assert len(priorities) > 0
    assert priorities[0]["category"] == "family"
    assert priorities[0]["student_status"] == "NOT_STARTED"

    # Now simulate bridged topic progress for the family's canonical name:
    # We add a topic for Quantum Logic Gates and mark it STARTED
    db = personalized_test_setup["TestingSessionLocal"]()
    syl = Syllabus(course_id=course_fam.id, version="v1")
    db.add(syl)
    db.commit()
    u = Unit(syllabus_id=syl.id, number=1, name="Quantum")
    db.add(u)
    db.commit()
    t = Topic(unit_id=u.id, name="Quantum Logic Gates")
    db.add(t)
    db.commit()
    prog = StudentTopicProgress(student_id=student_id, topic_id=t.id, status="STARTED", practice_attempted=2, practice_correct=2)
    db.add(prog)
    db.commit()
    db.close()

    # Now fetch personalized intelligence for course_fam_only
    resp_updated = client.get(f"/api/intelligence/{course_fam.id}?student_id={student_id}")
    assert resp_updated.status_code == 200
    updated_priorities = resp_updated.json()["study_priorities"]
    fam_priority = next(p for p in updated_priorities if p["name"] == "Quantum Logic Gates")

    assert fam_priority["student_status"] == "STARTED"
    assert fam_priority["practice_accuracy"] == 1.0


def test_cache_keys_do_not_collide_across_contexts():
    """H. Cache keys incorporate student_id and do not collide across distinct student contexts."""
    key_anon1 = build_cache_key(101, "CT1", "german")
    key_anon2 = build_cache_key(101, "CT1", "german", student_id="anonymous")
    key_anon3 = build_cache_key(101, "CT1", "german", student_id="   ")
    key_student1 = build_cache_key(101, "CT1", "german", student_id="student_1")
    key_student2 = build_cache_key(101, "CT1", "german", student_id="student_2")

    # Anonymous keys match each other
    assert key_anon1 == key_anon2 == key_anon3

    # Student keys differ from anonymous and differ from each other
    assert key_student1 != key_anon1
    assert key_student2 != key_anon1
    assert key_student1 != key_student2
    assert "student:student_1" in key_student1
    assert "student:student_2" in key_student2
