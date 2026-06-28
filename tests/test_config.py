"""Tests for the Settings loader."""

from __future__ import annotations

from app.config import get_settings


def test_settings_loaded() -> None:
    """Settings are loaded with sensible defaults under the test environment."""
    settings = get_settings()

    assert settings.app_name == "TradingOS"
    assert settings.app_env == "test"
    assert settings.database_url.startswith("sqlite")


def test_cors_origins_list_handles_wildcard() -> None:
    """The CORS helper returns ``['*']`` when the env value is a wildcard."""
    settings = get_settings()
    assert settings.cors_origins_list == ["*"]
