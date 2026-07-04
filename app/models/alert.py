"""Alert ORM model.

An ``Alert`` is a market event ingested from an external source (currently
TradingView via webhook). The model stores:

* the required, queryable fields (``symbol``, ``exchange``, ``signal`` ...);
* the raw payload as JSON (audit + replay);
* the AI analysis output as JSON (populated by the pipeline immediately
  after storage);
* a status flag driving the small state machine
  ``pending → analyzed → notified → archived``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utc_now_naive() -> datetime:
    """UTC ``datetime`` without tzinfo (single project-wide convention)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Allowed status values. Kept as a module-level tuple so tests and services
# can import the canonical list without duplicating string literals.
ALERT_STATUSES: tuple[str, ...] = ("pending", "analyzed", "notified", "archived")


class Alert(Base):
    """Market event alert ingested from an external source."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ---- Source identification -----------------------------------------
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, doc="Source identifier (e.g. 'tradingview')."
    )
    symbol: Mapped[str] = mapped_column(
        String(50), nullable=False, doc="Trading symbol. Stored upper-case."
    )
    exchange: Mapped[str] = mapped_column(
        String(20), nullable=False, doc="Exchange code (e.g. NSE). Upper-case."
    )
    signal: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Signal direction: 'BUY' or 'SELL'.",
    )

    # ---- Optional descriptive fields -----------------------------------
    timeframe: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    strategy: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # ---- Timestamps -----------------------------------------------------
    alert_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="Timestamp reported by the source (may differ from ingest time).",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=_utc_now_naive,
        doc="UTC timestamp when the server first stored the row.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=_utc_now_naive,
        onupdate=_utc_now_naive,
        doc="UTC timestamp updated on every write.",
    )

    # ---- Raw + derived payloads ----------------------------------------
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        doc="The full original payload, preserved for replay and debugging.",
    )
    analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="AI provider analysis (structure defined by AlertAnalysis schema).",
    )

    # ---- Lifecycle -----------------------------------------------------
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        doc="Lifecycle status. One of ALERT_STATUSES.",
    )

    __table_args__ = (
        Index("ix_alerts_created_at", "created_at"),
        Index("ix_alerts_symbol_created", "symbol", "created_at"),
        Index("ix_alerts_signal", "signal"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_source", "source"),
    )

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"Alert(id={self.id}, source={self.source!r}, symbol={self.symbol!r}, "
            f"signal={self.signal!r}, status={self.status!r})"
        )
