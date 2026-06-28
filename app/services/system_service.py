"""System service.

Encapsulates the small amount of logic backing the foundational endpoints
(``/``, ``/health``, ``/version``). Keeping this in a service — rather than
inline in the router — keeps the API layer thin and makes the behaviour easy
to unit-test in isolation.
"""

from __future__ import annotations

import platform

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings
from app.core.constants import BUILD, CODENAME
from app.schemas import HealthResponse, RootResponse, VersionResponse


class SystemService:
    """Read-only service exposing application metadata and health checks."""

    def __init__(self, settings: Settings) -> None:
        """Create the service."""
        self._settings = settings

    def root(self) -> RootResponse:
        """Build the payload for ``GET /``."""
        return RootResponse(
            name=self._settings.app_name,
            version=self._settings.app_version,
            environment=self._settings.app_env,
        )

    def health(self, db: Session) -> HealthResponse:
        """Build the payload for ``GET /health``. Probes the DB with SELECT 1."""
        db_status: str = "ok"
        try:
            db.execute(text("SELECT 1"))
        except Exception:  # pragma: no cover - defensive
            db_status = "error"

        overall: str = "ok" if db_status == "ok" else "degraded"
        return HealthResponse(status=overall, database=db_status)  # type: ignore[arg-type]

    def version(self) -> VersionResponse:
        """Build the payload for ``GET /version``."""
        return VersionResponse(
            name=self._settings.app_name,
            version=self._settings.app_version,
            build=BUILD,
            codename=CODENAME,
            environment=self._settings.app_env,
            python=platform.python_version(),
        )
