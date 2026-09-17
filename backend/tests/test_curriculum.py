import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import SessionLocal
from backend.models.core import Question, Exam, Course, QuestionFamily, CurriculumMapping


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_curriculum_branches(client: TestClient):
    resp = client.get("/api/curriculum/branches")
    assert resp.status_code == 200
    branches = resp.json()
    assert isinstance(branches, list)
    assert len(branches) == 54
    assert "Aerospace Engineering" in branches
    assert "Computer Science and Engineering" in branches
    assert "Civil Engineering" in branches


def test_curriculum_semesters(client: TestClient):
    # Valid branch
    resp = client.get("/api/curriculum/branches/Aerospace%20Engineering/semesters")
    assert resp.status_code == 200
    semesters = resp.json()
    assert isinstance(semesters, list)
    assert len(semesters) == 8
    assert semesters == [1, 2, 3, 4, 5, 6, 7, 8]

    # Invalid branch
    resp_404 = client.get("/api/curriculum/branches/NonExistentBranch/semesters")
    assert resp_404.status_code == 404


def test_curriculum_subjects_and_evidence(client: TestClient):
    # Aero Sem 1 -> Calculus should be MATCHED with >= 13 exams and >= 62 questions
    resp = client.get("/api/curriculum/branches/Aerospace%20Engineering/semesters/1")
    assert resp.status_code == 200
    subjects = resp.json()
    assert len(subjects) == 5

    calc = next((s for s in subjects if "Calculus" in s["subject_name"]), None)
    assert calc is not None
    assert calc["status"] == "MATCHED"
    assert calc["course_id"] == 1
    assert calc["canonical_code"] == "21MAB101T"
    assert calc["has_exams"] is True
    assert calc["exam_count"] >= 13
    assert calc["question_count"] >= 62

    # Aero Sem 1 -> EEE is MATCHED with Course 14
    eee = next((s for s in subjects if "Electrical" in s["subject_name"]), None)
    assert eee is not None
    assert eee["status"] == "MATCHED"
    assert eee["course_id"] == 14
    assert eee["has_exams"] is True

    # Aero Sem 2 -> Chemistry should be MATCHED with 4 exams and 197 questions
    resp_sem2 = client.get("/api/curriculum/branches/Aerospace%20Engineering/semesters/2")
    assert resp_sem2.status_code == 200
    subjects_sem2 = resp_sem2.json()

    chem = next((s for s in subjects_sem2 if s["subject_name"] == "Chemistry"), None)
    assert chem is not None
    assert chem["status"] == "MATCHED"
    assert chem["course_id"] == 2
    assert chem["canonical_code"] == "21CYB101J"
    assert chem["has_exams"] is True
    assert chem["exam_count"] >= 4
    assert chem["question_count"] >= 197

    # Biology should be AMBIGUOUS
    bio = next((s for s in subjects_sem2 if s["subject_name"] == "Biology"), None)
    assert bio is not None
    assert bio["status"] == "AMBIGUOUS"
    assert bio["course_id"] is None
    assert bio["notes"] is not None
    assert "General Biology" in bio["notes"]

    # Philosophy of Engineering should be MATCHED with historical exams
    phil = next((s for s in subjects_sem2 if "Philosophy" in s["subject_name"]), None)
    assert phil is not None
    assert phil["status"] == "MATCHED"
    assert phil["course_id"] == 3
    assert phil["has_exams"] is True
    assert phil["exam_count"] >= 10


def test_multi_branch_course_sharing(client: TestClient):
    """Verify that common courses across branches link to the same canonical backend Course."""
    db = SessionLocal()
    try:
        # Calculus and Linear Algebra across all branches
        calc_mappings = (
            db.query(CurriculumMapping)
            .filter(CurriculumMapping.course_id == 1)
            .all()
        )
        branches_with_calc = set(m.branch_name for m in calc_mappings)
        assert len(branches_with_calc) == 54
        assert len(calc_mappings) == 54

        # Chemistry across 53 branches
        chem_mappings = (
            db.query(CurriculumMapping)
            .filter(CurriculumMapping.course_id == 2)
            .all()
        )
        branches_with_chem = set(m.branch_name for m in chem_mappings)
        assert len(branches_with_chem) == 53
        assert len(chem_mappings) == 53
    finally:
        db.close()


def test_curriculum_stats(client: TestClient):
    resp = client.get("/api/curriculum/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_entries"] == 2810
    assert stats["branches_count"] == 54
    assert stats["matched_entries"] >= 250
    assert stats["ambiguous_entries"] == 40
    assert stats["backend_courses_count"] >= 23


def test_corpus_invariants_conserved():
    """Verify that existing questions, exams, courses, and families were not mutated or lost."""
    db = SessionLocal()
    try:
        assert db.query(Question).count() >= 7385
        assert db.query(Exam).count() >= 264
        assert db.query(Course).count() >= 23
        assert db.query(QuestionFamily).count() >= 6103
    finally:
        db.close()
