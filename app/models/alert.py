"""Alert ORM model.

An ``Alert`` is a market event ingested from an external source (currently
TradingView via webhook). The model stores both the parsed, queryable fields
and the original raw payload — the raw copy is retained so we can replay or
debug ingest without losing fidelity.

This is the first ORM model in TradingOS. The Alembic migration scaffold
will be introduced in the next sprint that needs a schema change; for Sprint 1
we lean on :func:`app.database.init_db.init_db` and ``Base.metadata.create_all``.
See ``docs/CTO_NOTES.md`` (T-001) for the deferral note.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utc_now_naive() -> datetime:
    """Return the current UTC time as a naive ``datetime``.

    SQLite stores naive datetimes; we keep a single convention across the
    codebase: every persisted timestamp is UTC, naive, and ISO 8601 when
    serialised to JSON.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Alert(Base):
    """Market event alert ingested from an external source."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Source identifier (e.g. 'tradingview').",
    )
    ticker: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Symbol the alert refers to. Stored upper-case.",
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Alert action (e.g. 'buy', 'sell', 'alert'). Stored lower-case.",
    )
    price: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Optional reference price reported with the alert.",
    )
    timeframe: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Optional timeframe identifier (e.g. '5m', '1h', '1D').",
    )
    strategy: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Optional strategy name that fired the alert.",
    )
    message: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        doc="Optional free-text message from the source.",
    )
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        doc="The full original payload, preserved for replay and debugging.",
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=_utc_now_naive,
        doc="UTC timestamp (naive) when the server ingested the alert.",
    )

    __table_args__ = (
        Index("ix_alerts_received_at", "received_at"),
        Index("ix_alerts_ticker_received", "ticker", "received_at"),
        Index("ix_alerts_source", "source"),
    )

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"Alert(id={self.id}, source={self.source!r}, ticker={self.ticker!r}, "
            f"action={self.action!r}, received_at={self.received_at!r})"
        )
