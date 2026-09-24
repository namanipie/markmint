import json
import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.database import SessionLocal
from backend.models.core import Course


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_backend_course_model_semester_property():
    """Verify that Course model computes authoritative semester metadata directly."""
    db = SessionLocal()
    try:
        # Semester 3 Courses
        course_dsa = db.query(Course).filter(Course.canonical_code == "21CSC201J").first()
        assert course_dsa is not None
        assert course_dsa.semester == 3

        course_os = db.query(Course).filter(Course.canonical_code == "21CSC202J").first()
        assert course_os is not None
        assert course_os.semester == 3

        course_coa = db.query(Course).filter(Course.canonical_code == "21CSS201T").first()
        assert course_coa is not None
        assert course_coa.semester == 3

        course_tbvp = db.query(Course).filter(Course.canonical_code == "21MAB201T").first()
        assert course_tbvp is not None
        assert course_tbvp.semester == 3

        # Semester 4 Courses
        course_daa = db.query(Course).filter(Course.canonical_code == "21CSC204J").first()
        assert course_daa is not None
        assert course_daa.semester == 4

        course_dbms = db.query(Course).filter(Course.canonical_code == "21CSC205P").first()
        assert course_dbms is not None
        assert course_dbms.semester == 4

        course_ai = db.query(Course).filter(Course.canonical_code == "21CSC207J").first()
        assert course_ai is not None
        assert course_ai.semester == 4

        course_pqt = db.query(Course).filter(Course.canonical_code == "21MAB204T").first()
        assert course_pqt is not None
        assert course_pqt.semester == 4

        # Probability and Statistics (Course 22)
        course_prob = db.query(Course).filter(Course.canonical_code == "21MAB202T").first()
        assert course_prob is not None
        assert course_prob.semester == 4
    finally:
        db.close()


def test_courses_api_endpoint_semesters(client: TestClient):
    """Verify that GET /api/courses returns authoritative semester numbers in JSON payload."""
    resp = client.get("/api/courses")
    assert resp.status_code == 200
    courses_by_code = {c["canonical_code"]: c for c in resp.json() if c.get("canonical_code")}

    # Semester 3 assertions
    assert courses_by_code["21CSC201J"]["semester"] == 3
    assert courses_by_code["21CSC202J"]["semester"] == 3
    assert courses_by_code["21CSS201T"]["semester"] == 3
    assert courses_by_code["21MAB201T"]["semester"] == 3

    # Semester 4 assertions
    assert courses_by_code["21CSC204J"]["semester"] == 4
    assert courses_by_code["21CSC205P"]["semester"] == 4
    assert courses_by_code["21CSC207J"]["semester"] == 4
    assert courses_by_code["21MAB204T"]["semester"] == 4

    # Probability and Statistics
    assert courses_by_code["21MAB202T"]["semester"] == 4


def test_regression_no_year2_courses_in_semester_2(client: TestClient):
    """
    CRITICAL REGRESSION TEST:
    Specifically prevents Year-2 courses (Semesters 3 and 4) from being
    misclassified or displayed under Semester 2.
    """
    resp = client.get("/api/courses")
    assert resp.status_code == 200
    courses = resp.json()

    year2_codes = [
        "21CSC201J",  # DSA (Sem 3)
        "21CSC202J",  # OS (Sem 3)
        "21CSS201T",  # COA (Sem 3)
        "21MAB201T",  # TBVP (Sem 3)
        "21CSC204J",  # DAA (Sem 4)
        "21CSC205P",  # DBMS (Sem 4)
        "21CSC207J",  # AI (Sem 4)
        "21MAB204T",  # PQT (Sem 4)
    ]

    for c in courses:
        code = c.get("canonical_code")
        if code in year2_codes:
            assert c["semester"] != 2, f"Regression: Year-2 course {c['name']} ({code}) is misclassified as Semester 2!"
            assert c["semester"] in (3, 4), f"Year-2 course {c['name']} ({code}) has unexpected semester {c['semester']}!"


def test_frontend_courses_catalog_fixture_grouping():
    """Verify that src/lib/courses-catalog.json has exact Year & Semester assignments."""
    catalog_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "src", "lib", "courses-catalog.json"
    )
    assert os.path.exists(catalog_path), f"Missing catalog file at {catalog_path}"

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    courses_by_code = {c["canonicalCode"]: c for c in catalog if c.get("canonicalCode")}

    # Validate exact semester assignments
    assert courses_by_code["21CSC201J"]["semester"] == 3
    assert courses_by_code["21CSC202J"]["semester"] == 3
    assert courses_by_code["21CSS201T"]["semester"] == 3
    assert courses_by_code["21MAB201T"]["semester"] == 3

    assert courses_by_code["21CSC204J"]["semester"] == 4
    assert courses_by_code["21CSC205P"]["semester"] == 4
    assert courses_by_code["21CSC207J"]["semester"] == 4
    assert courses_by_code["21MAB204T"]["semester"] == 4
    assert courses_by_code["21MAB202T"]["semester"] == 4

    # Grouping logic simulation: Year 2 -> Semester 3 & Semester 4
    sem3_courses = [c["name"] for c in catalog if c["semester"] == 3]
    sem4_courses = [c["name"] for c in catalog if c["semester"] == 4]

    assert "Data Structures and Algorithms" in sem3_courses
    assert "Operating Systems" in sem3_courses
    assert "Computer Organization and Architecture" in sem3_courses
    assert "Transforms and Boundary Value Problems" in sem3_courses

    assert "Design and Analysis of Algorithms" in sem4_courses
    assert "Database Management Systems" in sem4_courses
    assert "Artificial Intelligence" in sem4_courses
    assert "Probability and Queueing Theory" in sem4_courses
    assert "Probability and Statistics" in sem4_courses

    # Ensure zero overlap
    overlap = set(sem3_courses).intersection(set(sem4_courses))
    assert len(overlap) == 0, f"Detected overlapping courses between Sem 3 and Sem 4: {overlap}"
