"""Alert ORM model.

v0.3 additive-only columns (all nullable). Naming follows the CTO decision:

    ai_provider           str    provider name (e.g. "ollama", "mock")
    ai_model              str    model identifier
    ai_prompt             text   full LLM prompt sent
    ai_response           text   raw LLM output before validation
    analysis_latency_ms   int    wall-clock LLM latency
    analysis_version      str    version tag of the analysis pipeline
    prompt_version        str    version tag of the prompt template
    market_context        json   snapshot used to build the prompt
    token_count           int    prompt + completion tokens (when reported)

No renames or deletions of pre-v0.3 columns. Alembic is deferred (see
docs/KNOWN_ISSUES.md). Developers with a stale storage/tradingos.db must
delete it and let Base.metadata.create_all() recreate the schema.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utc_now_naive() -> datetime:
    """UTC ``datetime`` without tzinfo — project-wide convention."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


ALERT_STATUSES: tuple[str, ...] = ("pending", "analyzed", "notified", "archived")


class Alert(Base):
    """Market event alert ingested from an external source."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ---- Source identification (v0.2 stable) ---------------------------
    source:   Mapped[str] = mapped_column(String(50),  nullable=False)
    symbol:   Mapped[str] = mapped_column(String(50),  nullable=False)
    exchange: Mapped[str] = mapped_column(String(20),  nullable=False)
    signal:   Mapped[str] = mapped_column(String(10),  nullable=False)

    # ---- Optional descriptive fields (v0.2 stable) ---------------------
    timeframe: Mapped[Optional[str]] = mapped_column(String(20),  nullable=True)
    strategy:  Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    price:     Mapped[float]         = mapped_column(Float,       nullable=False)

    # ---- Timestamps (v0.2 stable) --------------------------------------
    alert_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at:      Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now_naive)
    updated_at:      Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now_naive, onupdate=_utc_now_naive)

    # ---- Payloads (v0.2 stable) ----------------------------------------
    raw_payload: Mapped[dict[str, Any]]             = mapped_column(JSON, nullable=False)
    analysis:    Mapped[Optional[dict[str, Any]]]   = mapped_column(JSON, nullable=True)

    # ---- Lifecycle (v0.2 stable) ---------------------------------------
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # ---- v0.3 Intelligence-layer columns (all nullable, additive) ------
    ai_provider:         Mapped[Optional[str]]            = mapped_column(String(30), nullable=True)
    ai_model:            Mapped[Optional[str]]            = mapped_column(String(60), nullable=True)
    ai_prompt:           Mapped[Optional[str]]            = mapped_column(Text,       nullable=True)
    ai_response:         Mapped[Optional[str]]            = mapped_column(Text,       nullable=True)
    analysis_latency_ms: Mapped[Optional[int]]            = mapped_column(Integer,    nullable=True)
    analysis_version:    Mapped[Optional[str]]            = mapped_column(String(30), nullable=True)
    prompt_version:      Mapped[Optional[str]]            = mapped_column(String(30), nullable=True)
    market_context:      Mapped[Optional[dict[str, Any]]] = mapped_column(JSON,       nullable=True)
    token_count:         Mapped[Optional[int]]            = mapped_column(Integer,    nullable=True)

    __table_args__ = (
        Index("ix_alerts_created_at",     "created_at"),
        Index("ix_alerts_symbol_created", "symbol", "created_at"),
        Index("ix_alerts_signal",         "signal"),
        Index("ix_alerts_status",         "status"),
        Index("ix_alerts_source",         "source"),
        # Indices for future experiment-tracking queries (cheap, additive):
        Index("ix_alerts_ai_model",         "ai_model"),
        Index("ix_alerts_prompt_version",   "prompt_version"),
        Index("ix_alerts_analysis_version", "analysis_version"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Alert(id={self.id}, source={self.source!r}, symbol={self.symbol!r}, "
            f"signal={self.signal!r}, status={self.status!r})"
        )
