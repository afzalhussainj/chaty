"""Health endpoint tests (readiness checks mocked — no DB/Redis required)."""

from __future__ import annotations

from unittest.mock import patch

from app.schemas.common import ComponentHealth
from fastapi.testclient import TestClient


def test_liveness(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.services.health_service.check_redis")
@patch("app.services.health_service.check_database")
def test_readiness_healthy(mock_db, mock_redis, client: TestClient) -> None:
    mock_db.return_value = ComponentHealth(name="database", status="up", latency_ms=1.0)
    mock_redis.return_value = ComponentHealth(name="redis", status="up", latency_ms=2.0)

    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["version"]
    assert body["environment"] == "test"
    assert len(body["dependencies"]) == 2


@patch("app.services.health_service.check_redis")
@patch("app.services.health_service.check_database")
def test_readiness_unhealthy(mock_db, mock_redis, client: TestClient) -> None:
    mock_db.return_value = ComponentHealth(
        name="database", status="down", error="connection refused"
    )
    mock_redis.return_value = ComponentHealth(name="redis", status="up", latency_ms=1.0)

    response = client.get("/api/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
