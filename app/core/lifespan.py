"""Application lifespan hooks.

FastAPI's lifespan context allows us to run code on startup and shutdown.
On startup we initialise the database, log a banner, and confirm the
configuration is loaded. On shutdown we release resources.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage the application's startup and shutdown sequence.

    Startup:
        * Configure structured logging.
        * Initialise the database (create tables if missing).
        * Emit a startup banner with environment metadata.

    Shutdown:
        * Emit a shutdown log line. (Resource cleanup hooks land here as the
          project grows.)
    """
    configure_logging()
    logger = get_logger("tradingos.lifespan")
    settings = get_settings()

    # ---- Startup --------------------------------------------------------
    db_ok = False
    try:
        init_db()
        db_ok = True
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("database.init.failed", error=str(exc))
        raise

    logger.info(
        "application.startup",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        debug=settings.app_debug,
        database_connected=db_ok,
        database_url=_redact_db_url(settings.database_url),
    )

    yield

    # ---- Shutdown -------------------------------------------------------
    logger.info("application.shutdown", app_name=settings.app_name)


def _redact_db_url(url: str) -> str:
    """Remove any embedded credentials before logging a database URL."""
    if "@" not in url:
        return url
    scheme, _, rest = url.partition("://")
    _, _, host_part = rest.partition("@")
    return f"{scheme}://***@{host_part}"
