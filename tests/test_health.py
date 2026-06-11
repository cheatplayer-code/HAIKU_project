"""Health endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    """Test that /health returns the expected response."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["service"] == "birge-api"
    assert data["status"] == "healthy"
