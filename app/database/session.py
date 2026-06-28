"""Database session & engine factory.

Provides:

* ``engine`` — process-wide SQLAlchemy engine bound to ``DATABASE_URL``.
* ``SessionLocal`` — session factory used by repositories and request handlers.
* ``Base`` — declarative base that all ORM models inherit from.
* ``get_db`` — FastAPI dependency that yields a scoped session per request.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


def _build_engine() -> Engine:
    """Construct the SQLAlchemy engine and ensure the SQLite parent dir exists."""
    settings = get_settings()
    url = settings.database_url

    connect_args: dict[str, Any] = {}
    engine_kwargs: dict[str, Any] = {
        "echo": settings.database_echo,
        "future": True,
    }

    if url.startswith("sqlite"):
        # Required for SQLite when used across threads (FastAPI dev server).
        connect_args["check_same_thread"] = False

        if ":memory:" in url:
            # In-memory SQLite needs a StaticPool — without it, each new
            # connection creates a fresh in-memory database and tables created
            # at startup vanish on the next checkout. This matters for tests
            # and for any other ephemeral usage.
            engine_kwargs["poolclass"] = StaticPool
        else:
            # File-backed SQLite: make sure the directory for the .db file
            # exists so the engine can create it.
            db_path = url.split("///", 1)[-1]
            if db_path:
                Path(db_path).expanduser().resolve().parent.mkdir(
                    parents=True, exist_ok=True
                )

    engine_kwargs["connect_args"] = connect_args
    return create_engine(url, **engine_kwargs)


engine: Engine = _build_engine()

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
