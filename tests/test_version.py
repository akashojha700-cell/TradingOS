"""Tests for ``GET /version``."""

from __future__ import annotations

import platform

from fastapi.testclient import TestClient

from app import __version__
from app.version import BUILD, CODENAME


def test_version_returns_build_metadata(client: TestClient) -> None:
    """Version endpoint returns app + runtime version info."""
    response = client.get("/version")
    assert response.status_code == 200

    body = response.json()
    assert body["name"] == "TradingOS"
    assert body["version"] == __version__
    assert body["build"] == BUILD
    assert body["codename"] == CODENAME
    assert body["environment"] == "test"
    assert body["python"] == platform.python_version()
