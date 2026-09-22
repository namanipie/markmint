from fastapi.testclient import TestClient


def test_health_check_get(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_head(client: TestClient) -> None:
    response = client.head("/api/health")
    assert response.status_code == 200
    assert response.text == ""


def test_root_health_check_get(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_root_health_check_head(client: TestClient) -> None:
    response = client.head("/health")
    assert response.status_code == 200
    assert response.text == ""
