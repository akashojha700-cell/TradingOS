"""Application lifespan hooks.

FastAPI's lifespan context runs code on startup and shutdown. Startup:
initialise structured logging, ensure the database schema exists, emit a
banner, and print the resolved AI provider config so operators can confirm
their ``.env`` values landed correctly (e.g. Ollama host / model / timeout).
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
    """Manage the application's startup and shutdown sequence."""
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

    # Resolved AI provider config — logged loudly at INFO so any misconfigured
    # env var (e.g. OLLAMA_TIMEOUT missing → default 60s applied) is spotted
    # immediately on boot instead of much later when a request times out.
    logger.info(
        "ai.provider.configured",
        provider=settings.ai_provider,
        ollama_host=settings.ollama_host,
        ollama_model=settings.ollama_model,
        ollama_timeout_seconds=float(settings.ollama_timeout_seconds),
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
