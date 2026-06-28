"""Shared pytest fixtures.

Tests run against an isolated in-memory SQLite database. The application's
engine uses ``StaticPool`` for in-memory URLs, so connections share one
database — we therefore drop and re-create the schema before each test to
guarantee isolation.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

# ---- Environment isolation ----------------------------------------------
# Set BEFORE importing the application so settings pick up the test values.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("LOG_JSON", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.database.session import Base, engine as app_engine  # noqa: E402
from app.main import create_app  # noqa: E402

# Ensure models are registered with Base.metadata before any create_all().
import app.models  # noqa: E402, F401


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    """Ensure the settings cache is clean between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _fresh_schema() -> Iterator[None]:
    """Drop and re-create all tables on the application engine.

    Required because the in-memory SQLite engine uses StaticPool (a single
    shared connection) — so DB state persists across tests by default.
    """
    Base.metadata.drop_all(app_engine)
    Base.metadata.create_all(app_engine)
    yield


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """A FastAPI ``TestClient`` bound to a fresh application instance."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def client_with_secret(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """A client whose underlying app has a webhook secret configured."""
    secret = "test-secret-token-123"
    monkeypatch.setenv("TRADINGVIEW_WEBHOOK_SECRET", secret)
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as test_client:
        test_client.app.state.webhook_secret = secret  # type: ignore[attr-defined]
        yield test_client


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """Yield a session bound to a *fresh* in-memory SQLite engine.

    Used by repository / service unit tests that should not go through the
    FastAPI app. Each test gets its own engine — total isolation.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, class_=Session
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
