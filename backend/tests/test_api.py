import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_create_course(client: TestClient) -> None:
    pass

def test_get_dna(client: TestClient) -> None:
    # 404 for non-existent course
    response = client.get("/api/analysis/dna?course_id=999")
    assert response.status_code == 404

    # 200 for numeric course_id
    response_calc = client.get("/api/analysis/dna?course_id=1")
    assert response_calc.status_code == 200
    data = response_calc.json()
    assert "sample_size" in data

    # 200 for string course name / code
    response_str = client.get("/api/analysis/dna?course_id=SEM1-CALC")
    assert response_str.status_code == 200

def test_get_predictions(client: TestClient) -> None:
    # 404 for non-existent subject
    response = client.get("/api/predictions/NonExistentSubject")
    assert response.status_code == 404

    # 200 for exact canonical name
    resp_exact = client.get("/api/predictions/Calculus%20And%20Linear%20Algebra")
    assert resp_exact.status_code == 200
    assert resp_exact.json()["subject"] == "Calculus And Linear Algebra"

    # 200 for case-variant curriculum name
    resp_case = client.get("/api/predictions/Calculus%20and%20Linear%20Algebra")
    assert resp_case.status_code == 200
    assert resp_case.json()["subject"] == "Calculus And Linear Algebra"

    # 200 for course code
    resp_code = client.get("/api/predictions/SEM1-CALC")
    assert resp_code.status_code == 200
    assert resp_code.json()["subject"] == "Calculus And Linear Algebra"

