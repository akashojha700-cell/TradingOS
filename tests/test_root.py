"""Tests for the root URL (HTML SPA) and the moved ``/api/v1/info`` banner."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_root_serves_html_ui(client: TestClient) -> None:
    """The root URL returns the TradingOS single-page application."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert '<div id="root"' in body
    assert "TradingOS" in body


def test_root_sets_request_id_header(client: TestClient) -> None:
    """Every response is tagged with a correlation ID."""
    response = client.get("/")
    assert response.headers.get("X-Request-ID")


def test_info_endpoint_returns_service_banner(client: TestClient) -> None:
    """The JSON service banner lives at /api/v1/info."""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "TradingOS"
    assert "version" in body
    assert body["environment"] == "test"
    assert body["docs_url"] == "/docs"
