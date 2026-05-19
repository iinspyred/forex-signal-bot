import os

from fastapi.testclient import TestClient

os.environ.setdefault("TWELVEDATA_API_KEY", "test")
os.environ.setdefault("FINNHUB_API_KEY", "test")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("TELEGRAM_CHAT_ID", "12345")

from app.main import app  # noqa: E402

client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "forex-signal-bot"
    assert "uptime" in data


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_stats_endpoint() -> None:
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "pairs" in data
    assert isinstance(data["pairs"], list)
