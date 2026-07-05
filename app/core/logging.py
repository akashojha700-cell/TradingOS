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
from pathlib import Path
from typing import Any, IO

import structlog

from app.config import get_settings

#: Application log file. Written in addition to stdout so operators always have
#: a persistent, greppable record (look for ``ai.ollama.raw_response`` /
#: ``ai.ollama.validator_input`` / ``analysis.fallback_used``). Resolved from
#: the project root so it is independent of the current working directory.
LOG_DIR: Path = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE: Path = LOG_DIR / "tradingos.log"


class _Tee:
    """Minimal write-through stream that fans out to several file objects."""

    def __init__(self, *streams: IO[str]) -> None:
        self._streams = streams

    def write(self, data: str) -> int:
        for s in self._streams:
            s.write(data)
            s.flush()
        return len(data)

    def flush(self) -> None:
        for s in self._streams:
            s.flush()


def configure_logging() -> None:
    """Configure stdlib ``logging`` and ``structlog`` for the whole process.

    Safe to call multiple times; structlog handles idempotency internally.
    Logs are emitted to stdout AND appended to ``logs/tradingos.log``.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # ---- Persistent log file (best-effort; never blocks startup) ---------
    log_stream: Any = sys.stdout
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        _fh = open(LOG_FILE, "a", encoding="utf-8")  # noqa: SIM115 (process-lifetime handle)
        log_stream = _Tee(sys.stdout, _fh)
    except OSError:
        # Read-only FS or permission issue — fall back to stdout only.
        log_stream = sys.stdout

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
        logger_factory=structlog.PrintLoggerFactory(file=log_stream),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger.

    Args:
        name: Optional logger name. Defaults to the calling module.
    """
    return structlog.get_logger(name)
