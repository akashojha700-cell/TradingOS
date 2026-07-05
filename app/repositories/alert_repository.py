"""Repository for the Alert aggregate."""

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
        alert = Alert(
            source=source, symbol=symbol, exchange=exchange, signal=signal, price=price,
            timeframe=timeframe, strategy=strategy, alert_timestamp=alert_timestamp,
            raw_payload=raw_payload, analysis=analysis, status=status,
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
        market_context: Optional[dict[str, Any]] = None,
        ai_prompt: Optional[str] = None,
        ai_response: Optional[str] = None,
        ai_provider: Optional[str] = None,
        ai_model: Optional[str] = None,
        analysis_latency_ms: Optional[int] = None,
        analysis_version: Optional[str] = None,
        prompt_version: Optional[str] = None,
        token_count: Optional[int] = None,
    ) -> Alert:
        """Attach analysis + CTO-approved intelligence metadata."""
        alert.analysis            = analysis
        alert.status              = status
        alert.market_context      = market_context      if market_context      is not None else alert.market_context
        alert.ai_prompt           = ai_prompt           if ai_prompt           is not None else alert.ai_prompt
        alert.ai_response         = ai_response         if ai_response         is not None else alert.ai_response
        alert.ai_provider         = ai_provider         if ai_provider         is not None else alert.ai_provider
        alert.ai_model            = ai_model            if ai_model            is not None else alert.ai_model
        alert.analysis_latency_ms = analysis_latency_ms if analysis_latency_ms is not None else alert.analysis_latency_ms
        alert.analysis_version    = analysis_version    if analysis_version    is not None else alert.analysis_version
        alert.prompt_version      = prompt_version      if prompt_version      is not None else alert.prompt_version
        alert.token_count         = token_count         if token_count         is not None else alert.token_count
        self._db.add(alert)
        self._db.commit()
        self._db.refresh(alert)
        return alert

    def delete(self, alert: Alert) -> None:
        self._db.delete(alert)
        self._db.commit()

    # ------------------------------------------------------------------ reads
    def get_by_id(self, alert_id: int) -> Optional[Alert]:
        return self._db.get(Alert, alert_id)

    def get_recent(self, *, limit: int = 10) -> list[Alert]:
        stmt = select(Alert).order_by(Alert.created_at.desc(), Alert.id.desc()).limit(limit)
        return list(self._db.execute(stmt).scalars().all())

    def list(
        self, *, limit: int = 50, offset: int = 0,
        symbol: Optional[str] = None, signal: Optional[str] = None,
        source: Optional[str] = None, status: Optional[str] = None,
    ) -> list[Alert]:
        stmt = (
            select(Alert)
            .order_by(Alert.created_at.desc(), Alert.id.desc())
            .limit(limit).offset(offset)
        )
        if symbol: stmt = stmt.where(Alert.symbol == symbol.strip().upper())
        if signal: stmt = stmt.where(Alert.signal == signal.strip().upper())
        if source: stmt = stmt.where(Alert.source == source)
        if status: stmt = stmt.where(Alert.status == status)
        return list(self._db.execute(stmt).scalars().all())

    def count(
        self, *,
        symbol: Optional[str] = None, signal: Optional[str] = None,
        source: Optional[str] = None, status: Optional[str] = None,
    ) -> int:
        stmt = select(func.count(Alert.id))
        if symbol: stmt = stmt.where(Alert.symbol == symbol.strip().upper())
        if signal: stmt = stmt.where(Alert.signal == signal.strip().upper())
        if source: stmt = stmt.where(Alert.source == source)
        if status: stmt = stmt.where(Alert.status == status)
        return int(self._db.execute(stmt).scalar_one())
