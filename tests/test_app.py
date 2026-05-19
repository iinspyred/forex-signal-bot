from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AI Forex Signal Bot"
    assert data["status"] == "online"


def test_health_endpoint() -> None:
    with TestClient(app) as lifespan_client:
        response = lifespan_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"healthy", "starting"}


def test_stats_endpoint() -> None:
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "active_pairs" in data
    assert isinstance(data["active_pairs"], list)
