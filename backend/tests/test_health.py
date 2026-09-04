"""Tests for the health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test root GET /health returns status 200 and structured response."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Revenue Autopsy"
    assert "environment" in payload


def test_versioned_health_endpoint():
    """Test GET /api/v1/health returns status 200 and structured response."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Revenue Autopsy"
    assert "environment" in payload
