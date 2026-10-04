import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import settings
from backend.core.database import get_db
from backend.main import app
from backend.models.core import CurriculumMapping, Course


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


def test_cse_semester_1_to_8_registration(prod_db: Session):
    """Verify Computer Science and Engineering has legitimate subjects across semesters 1 to 8."""
    cse_rows = (
        prod_db.query(CurriculumMapping)
        .filter(CurriculumMapping.branch_name == "Computer Science and Engineering")
        .order_by(CurriculumMapping.semester.asc(), CurriculumMapping.subject_name.asc())
        .all()
    )

    assert len(cse_rows) > 0, "CSE curriculum mappings must exist in database"
    semesters_present = {r.semester for r in cse_rows}
    for sem in range(1, 9):
        assert sem in semesters_present, f"Semester {sem} must be registered for CSE"


def test_cse_core_courses_mapped_correctly(prod_db: Session):
    """Verify that verified 2nd-year core CS courses are mapped to authentic course IDs."""
    sem3_courses = (
        prod_db.query(CurriculumMapping.subject_name, CurriculumMapping.course_id)
        .filter(
            CurriculumMapping.branch_name == "Computer Science and Engineering",
            CurriculumMapping.semester == 3,
        )
        .all()
    )
    s3_map = {name: cid for name, cid in sem3_courses}

    assert s3_map.get("Data Structures and Algorithms") == 24
    assert s3_map.get("Operating Systems") == 25
    assert s3_map.get("Computer Organization and Architecture") == 26
    assert s3_map.get("Transforms and Boundary Value Problems") == 30

    sem4_courses = (
        prod_db.query(CurriculumMapping.subject_name, CurriculumMapping.course_id)
        .filter(
            CurriculumMapping.branch_name == "Computer Science and Engineering",
            CurriculumMapping.semester == 4,
        )
        .all()
    )
    s4_map = {name: cid for name, cid in sem4_courses}

    assert s4_map.get("Design and Analysis of Algorithms") == 27
    assert s4_map.get("Database Management Systems") == 28
    assert s4_map.get("Artificial Intelligence") == 29
    assert s4_map.get("Probability and Queueing Theory") == 31


def test_no_departmental_misattribution_in_cse(prod_db: Session):
    """Ensure non-CS subjects (e.g. Bioprocess Engineering, Building Materials) are not assigned as CS core."""
    cse_names = {
        r.subject_name.lower()
        for r in prod_db.query(CurriculumMapping)
        .filter(CurriculumMapping.branch_name == "Computer Science and Engineering")
        .all()
    }

    assert "bioprocess engineering" not in cse_names
    assert "chemical engineering principles" not in cse_names
    assert "building materials in the built environment" not in cse_names


def test_curriculum_api_endpoint_semesters(prod_client: TestClient):
    """Test /api/curriculum/branches/{branch}/semesters returns full semester list."""
    res = prod_client.get("/api/curriculum/branches/Computer%20Science%20and%20Engineering/semesters")
    assert res.status_code == 200
    sems = res.json()
    assert isinstance(sems, list)
    for sem in range(1, 9):
        assert sem in sems
