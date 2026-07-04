"""Repository for the Alert aggregate.

Only this module talks to SQLAlchemy for the Alert resource. Services depend
on this class via dependency injection; routers do not.
"""

from __future__ import annotations

from datetime import datetime
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
        symbol: str,
        exchange: str,
        signal: str,
        price: float,
        timeframe: Optional[str] = None,
        strategy: Optional[str] = None,
        alert_timestamp: Optional[datetime] = None,
        raw_payload: dict[str, Any],
        analysis: Optional[dict[str, Any]] = None,
        status: str = "pending",
    ) -> Alert:
        """Insert and return a new :class:`Alert`."""
        alert = Alert(
            source=source,
            symbol=symbol,
            exchange=exchange,
            signal=signal,
            price=price,
            timeframe=timeframe,
            strategy=strategy,
            alert_timestamp=alert_timestamp,
            raw_payload=raw_payload,
            analysis=analysis,
            status=status,
        )
        self._db.add(alert)
        self._db.commit()
        self._db.refresh(alert)
        return alert

    def update_analysis(
        self,
        alert: Alert,
        *,
        analysis: dict[str, Any],
        status: str = "analyzed",
    ) -> Alert:
        """Attach an analysis payload to an existing alert and update status."""
        alert.analysis = analysis
        alert.status = status
        self._db.add(alert)
        self._db.commit()
        self._db.refresh(alert)
        return alert

    def delete(self, alert: Alert) -> None:
        """Delete an alert row. Callers are responsible for existence checks."""
        self._db.delete(alert)
        self._db.commit()

    # ------------------------------------------------------------------ reads
    def get_by_id(self, alert_id: int) -> Optional[Alert]:
        """Return the alert with the given id, or ``None`` if not found."""
        return self._db.get(Alert, alert_id)

    def get_recent(self, *, limit: int = 10) -> list[Alert]:
        """Return the ``limit`` most recently ingested alerts, newest first."""
        stmt = (
            select(Alert)
            .order_by(Alert.created_at.desc(), Alert.id.desc())
            .limit(limit)
        )
        return list(self._db.execute(stmt).scalars().all())

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        symbol: Optional[str] = None,
        signal: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[Alert]:
        """Return alerts newest-first, optionally filtered."""
        stmt = (
            select(Alert)
            .order_by(Alert.created_at.desc(), Alert.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if symbol:
            stmt = stmt.where(Alert.symbol == symbol.strip().upper())
        if signal:
            stmt = stmt.where(Alert.signal == signal.strip().upper())
        if source:
            stmt = stmt.where(Alert.source == source)
        if status:
            stmt = stmt.where(Alert.status == status)
        return list(self._db.execute(stmt).scalars().all())

    def count(
        self,
        *,
        symbol: Optional[str] = None,
        signal: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count alerts matching the (optional) filters."""
        stmt = select(func.count(Alert.id))
        if symbol:
            stmt = stmt.where(Alert.symbol == symbol.strip().upper())
        if signal:
            stmt = stmt.where(Alert.signal == signal.strip().upper())
        if source:
            stmt = stmt.where(Alert.source == source)
        if status:
            stmt = stmt.where(Alert.status == status)
        return int(self._db.execute(stmt).scalar_one())
