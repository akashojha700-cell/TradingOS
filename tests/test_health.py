"""Tests for ``GET /health``."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_reports_ok(client: TestClient) -> None:
    """Health endpoint returns ``ok`` when DB is reachable."""
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert "timestamp" in body


def test_health_echoes_custom_request_id(client: TestClient) -> None:
    """A caller-supplied X-Request-ID is preserved in the response."""
    response = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert response.headers["X-Request-ID"] == "abc-123"
