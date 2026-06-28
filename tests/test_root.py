"""Tests for ``GET /``."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_root_returns_service_banner(client: TestClient) -> None:
    """The root endpoint returns app metadata."""
    response = client.get("/")
    assert response.status_code == 200

    body = response.json()
    assert body["name"] == "TradingOS"
    assert "version" in body
    assert body["environment"] == "test"
    assert body["docs_url"] == "/docs"


def test_root_sets_request_id_header(client: TestClient) -> None:
    """Every response is tagged with a correlation ID."""
    response = client.get("/")
    assert response.headers.get("X-Request-ID")
