"""Repository for the Alert aggregate.

Only this module talks to SQLAlchemy for the Alert resource. Services depend
on this class via dependency injection; routers do not.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert import Alert


class AlertRepository:
    """SQLAlchemy-backed persistence for :class:`Alert`."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------ writes
    def create(
        self,
        *,
        source: str,
        ticker: str,
        action: str,
        price: Optional[float],
        timeframe: Optional[str],
        strategy: Optional[str],
        message: Optional[str],
        raw_payload: dict[str, Any],
    ) -> Alert:
        """Insert and return a new :class:`Alert`."""
        alert = Alert(
            source=source,
            ticker=ticker,
            action=action,
            price=price,
            timeframe=timeframe,
            strategy=strategy,
            message=message,
            raw_payload=raw_payload,
        )
        self._db.add(alert)
        self._db.commit()
        self._db.refresh(alert)
        return alert

    # ------------------------------------------------------------------ reads
    def get(self, alert_id: int) -> Optional[Alert]:
        """Return the alert with the given id, or ``None`` if not found."""
        return self._db.get(Alert, alert_id)

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        ticker: Optional[str] = None,
        source: Optional[str] = None,
    ) -> list[Alert]:
        """Return alerts newest-first, optionally filtered by ticker/source."""
        stmt = (
            select(Alert)
            .order_by(Alert.received_at.desc(), Alert.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if ticker:
            stmt = stmt.where(Alert.ticker == ticker.strip().upper())
        if source:
            stmt = stmt.where(Alert.source == source)
        return list(self._db.execute(stmt).scalars().all())

    def count(
        self,
        *,
        ticker: Optional[str] = None,
        source: Optional[str] = None,
    ) -> int:
        """Count alerts matching the (optional) filters."""
        stmt = select(func.count(Alert.id))
        if ticker:
            stmt = stmt.where(Alert.ticker == ticker.strip().upper())
        if source:
            stmt = stmt.where(Alert.source == source)
        return int(self._db.execute(stmt).scalar_one())
