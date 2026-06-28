"""Business logic for ingesting and exposing market event alerts."""

from __future__ import annotations

from typing import Any, Optional

from app.core.constants import SOURCE_TRADINGVIEW
from app.core.logging import get_logger
from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import TradingViewAlertIn

logger = get_logger("tradingos.alert_service")


class AlertNotFoundError(Exception):
    """Raised when an alert lookup misses."""

    def __init__(self, alert_id: int) -> None:
        super().__init__(f"Alert {alert_id} not found")
        self.alert_id = alert_id


class AlertService:
    """Orchestrates persistence and retrieval of alerts."""

    def __init__(self, repo: AlertRepository) -> None:
        self._repo = repo

    # ------------------------------------------------------------------ ingest
    def ingest_tradingview(
        self,
        *,
        raw_payload: dict[str, Any],
        parsed: TradingViewAlertIn,
    ) -> Alert:
        """Persist a TradingView alert and log the ingest event."""
        alert = self._repo.create(
            source=SOURCE_TRADINGVIEW,
            ticker=parsed.ticker,
            action=parsed.action,
            price=parsed.price,
            timeframe=parsed.timeframe,
            strategy=parsed.strategy,
            message=parsed.message,
            raw_payload=raw_payload,
        )
        logger.info(
            "alert.received",
            alert_id=alert.id,
            source=alert.source,
            ticker=alert.ticker,
            action=alert.action,
            timeframe=alert.timeframe,
        )
        return alert

    # ------------------------------------------------------------------ reads
    def get(self, alert_id: int) -> Alert:
        """Return one alert or raise :class:`AlertNotFoundError`."""
        alert = self._repo.get(alert_id)
        if alert is None:
            raise AlertNotFoundError(alert_id)
        return alert

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        ticker: Optional[str] = None,
        source: Optional[str] = None,
    ) -> tuple[list[Alert], int]:
        """Return a page of alerts together with the total matching count."""
        items = self._repo.list(
            limit=limit, offset=offset, ticker=ticker, source=source
        )
        total = self._repo.count(ticker=ticker, source=source)
        return items, total
