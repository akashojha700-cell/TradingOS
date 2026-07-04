"""Business logic for ingesting, analysing, and exposing market event alerts.

The Sprint 1 pipeline runs synchronously inside a single request:

    payload → validation → storage (pending)
            → context assembly → mock AI analysis
            → persistence update (analyzed) → response

Later sprints replace the synchronous mock call with either a background
worker or a real provider. The service surface stays the same.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.constants import BUILD, CODENAME, SOURCE_TRADINGVIEW, VERSION
from app.core.logging import get_logger
from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import (
    AlertAnalysis,
    AlertOut,
    StatisticsOut,
    TradingViewAlertIn,
)
from app.services.ai.base import AIProvider

logger = get_logger("tradingos.alert_service")


class AlertNotFoundError(Exception):
    """Raised when an alert lookup misses."""

    def __init__(self, alert_id: int) -> None:
        super().__init__(f"Alert {alert_id} not found")
        self.alert_id = alert_id


class AlertService:
    """Orchestrates ingest, storage, analysis, and retrieval of alerts."""

    def __init__(self, repo: AlertRepository, ai: AIProvider) -> None:
        self._repo = repo
        self._ai = ai

    # ------------------------------------------------------------------ ingest
    def ingest_tradingview(
        self,
        *,
        raw_payload: dict[str, Any],
        parsed: TradingViewAlertIn,
    ) -> Alert:
        """Store the alert, run the mock/real AI analysis, persist it back."""
        # ---- 1. Persist (status = pending) -----------------------------
        alert = self._repo.create(
            source=SOURCE_TRADINGVIEW,
            symbol=parsed.symbol,
            exchange=parsed.exchange,
            signal=parsed.signal,
            price=parsed.price,
            timeframe=parsed.timeframe,
            strategy=parsed.strategy,
            alert_timestamp=parsed.timestamp,
            raw_payload=raw_payload,
            status="pending",
        )
        logger.info(
            "alert.stored",
            alert_id=alert.id,
            source=alert.source,
            symbol=alert.symbol,
            signal=alert.signal,
            status=alert.status,
        )

        # ---- 2. Build the market context ------------------------------
        context = self._build_context(parsed)

        # ---- 3. Ask the AI provider -----------------------------------
        analysis = self._ai.analyze(alert_data=context)
        logger.info(
            "alert.analyzed",
            alert_id=alert.id,
            provider=analysis.provider,
            recommendation=analysis.recommendation,
            confidence=analysis.confidence,
            risk=analysis.risk,
        )

        # ---- 4. Attach analysis + advance status ----------------------
        alert = self._repo.update_analysis(
            alert,
            analysis=analysis.model_dump(),
            status="analyzed",
        )
        return alert

    def _build_context(self, parsed: TradingViewAlertIn) -> dict[str, Any]:
        """Assemble the dict handed to the AI provider.

        Kept as a separate method so future sprints can enrich the context
        (indicator snapshots, recent alerts, portfolio state) without
        touching the ingest flow.
        """
        return {
            "symbol": parsed.symbol,
            "exchange": parsed.exchange,
            "signal": parsed.signal,
            "price": parsed.price,
            "timeframe": parsed.timeframe,
            "strategy": parsed.strategy,
            "timestamp": parsed.timestamp.isoformat() if parsed.timestamp else None,
        }

    # ------------------------------------------------------------------ reads
    def get_by_id(self, alert_id: int) -> Alert:
        """Return one alert or raise :class:`AlertNotFoundError`."""
        alert = self._repo.get_by_id(alert_id)
        if alert is None:
            raise AlertNotFoundError(alert_id)
        return alert

    def get_recent(self, *, limit: int = 10) -> list[Alert]:
        """Return the ``limit`` most recent alerts."""
        return self._repo.get_recent(limit=limit)

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        symbol: Optional[str] = None,
        signal: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Alert], int]:
        """Return a page of alerts together with the total matching count."""
        items = self._repo.list(
            limit=limit,
            offset=offset,
            symbol=symbol,
            signal=signal,
            source=source,
            status=status,
        )
        total = self._repo.count(
            symbol=symbol, signal=signal, source=source, status=status
        )
        return items, total

    # ------------------------------------------------------------------ writes
    def delete(self, alert_id: int) -> None:
        """Delete an alert or raise :class:`AlertNotFoundError`."""
        alert = self._repo.get_by_id(alert_id)
        if alert is None:
            raise AlertNotFoundError(alert_id)
        self._repo.delete(alert)
        logger.info("alert.deleted", alert_id=alert_id)

    # ------------------------------------------------------------------ stats
    def statistics(self) -> StatisticsOut:
        """Build the summary payload for ``GET /api/v1/statistics``."""
        total = self._repo.count()
        buy = self._repo.count(signal="BUY")
        sell = self._repo.count(signal="SELL")
        recent = self._repo.get_recent(limit=1)
        latest_out = AlertOut.model_validate(recent[0]) if recent else None
        return StatisticsOut(
            total_alerts=total,
            buy_alerts=buy,
            sell_alerts=sell,
            latest_alert=latest_out,
            application_version=VERSION,
            build=BUILD,
            codename=CODENAME,
        )
