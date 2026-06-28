"""Structured logging configuration.

Uses ``structlog`` layered on top of the standard library ``logging`` module so
that every log record — whether emitted by application code, FastAPI, or
third-party libraries — flows through the same processor chain.

Two output modes are supported:

* **Console renderer** (``LOG_JSON=false``) — human-friendly during development.
* **JSON renderer** (``LOG_JSON=true``) — machine-parseable for production log
  aggregation.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from app.config import get_settings


def configure_logging() -> None:
    """Configure stdlib ``logging`` and ``structlog`` for the whole process.

    Safe to call multiple times; structlog handles idempotency internally.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # ---- Stdlib logging baseline ----------------------------------------
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )

    # Quiet noisy loggers a bit; let our own logs dominate.
    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).setLevel(max(log_level, logging.INFO))

    # ---- structlog processor chain --------------------------------------
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if settings.log_json
        else structlog.dev.ConsoleRenderer(colors=False)
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger.

    Args:
        name: Optional logger name. Defaults to the calling module.
    """
    return structlog.get_logger(name)
