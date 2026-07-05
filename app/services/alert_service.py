"""Alert service — persists inbound alerts and delegates analysis."""

from __future__ import annotations

from typing import Any, Optional

from app.core.constants import BUILD, CODENAME, SOURCE_TRADINGVIEW, VERSION
from app.core.logging import get_logger
from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertOut, StatisticsOut, TradingViewAlertIn
from app.services.analysis_service import AnalysisService

logger = get_logger("tradingos.alert_service")


class AlertNotFoundError(Exception):
    def __init__(self, alert_id: int) -> None:
        super().__init__(f"Alert {alert_id} not found")
        self.alert_id = alert_id


class AlertService:
    def __init__(self, *, repo: AlertRepository, analysis: AnalysisService) -> None:
        self._repo = repo
        self._analysis = analysis

    def ingest_tradingview(
        self, *, raw_payload: dict[str, Any], parsed: TradingViewAlertIn,
    ) -> Alert:
        # 1. Store raw alert (status = pending)
        alert = self._repo.create(
            source=SOURCE_TRADINGVIEW,
            symbol=parsed.symbol, exchange=parsed.exchange, signal=parsed.signal,
            price=parsed.price, timeframe=parsed.timeframe, strategy=parsed.strategy,
            alert_timestamp=parsed.timestamp, raw_payload=raw_payload, status="pending",
        )
        logger.info(
            "alert.stored", alert_id=alert.id, source=alert.source,
            symbol=alert.symbol, signal=alert.signal, status=alert.status,
        )

        # 2. Run pipeline
        result = self._analysis.analyze(parsed)

        # 3. Persist analysis + CTO-approved intelligence metadata
        alert = self._repo.update_analysis(
            alert,
            analysis=result.analysis.model_dump(),
            status="analyzed",
            market_context=result.market_context.model_dump(mode="json"),
            ai_prompt=result.prompt,
            ai_response=result.raw_response,
            ai_provider=result.provider,
            ai_model=result.model,
            analysis_latency_ms=result.latency_ms,
            analysis_version=result.analysis_version,
            prompt_version=result.prompt_version,
            token_count=result.token_count,
        )
        logger.info(
            "alert.analyzed",
            alert_id=alert.id, ai_provider=result.provider, ai_model=result.model,
            analysis_latency_ms=result.latency_ms, tokens=result.token_count,
            recommendation=result.analysis.recommendation,
            confidence=result.analysis.confidence, risk=result.analysis.risk,
            prompt_version=result.prompt_version, analysis_version=result.analysis_version,
        )
        return alert

    def get_by_id(self, alert_id: int) -> Alert:
        a = self._repo.get_by_id(alert_id)
        if a is None:
            raise AlertNotFoundError(alert_id)
        return a

    def get_recent(self, *, limit: int = 10) -> list[Alert]:
        return self._repo.get_recent(limit=limit)

    def list(
        self, *, limit: int = 50, offset: int = 0,
        symbol: Optional[str] = None, signal: Optional[str] = None,
        source: Optional[str] = None, status: Optional[str] = None,
    ) -> tuple[list[Alert], int]:
        items = self._repo.list(
            limit=limit, offset=offset,
            symbol=symbol, signal=signal, source=source, status=status,
        )
        total = self._repo.count(symbol=symbol, signal=signal, source=source, status=status)
        return items, total

    def delete(self, alert_id: int) -> None:
        a = self._repo.get_by_id(alert_id)
        if a is None:
            raise AlertNotFoundError(alert_id)
        self._repo.delete(a)
        logger.info("alert.deleted", alert_id=alert_id)

    def statistics(self) -> StatisticsOut:
        total = self._repo.count()
        buy   = self._repo.count(signal="BUY")
        sell  = self._repo.count(signal="SELL")
        recent = self._repo.get_recent(limit=1)
        latest_out = AlertOut.model_validate(recent[0]) if recent else None
        return StatisticsOut(
            total_alerts=total, buy_alerts=buy, sell_alerts=sell,
            latest_alert=latest_out,
            application_version=VERSION, build=BUILD, codename=CODENAME,
        )
