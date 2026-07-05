"""AlertService with the v0.3 AnalysisService pipeline (CTO-approved names)."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import TradingViewAlertIn
from app.services.ai import JsonValidator, MockAIProvider, PromptBuilder
from app.services.alert_service import AlertNotFoundError, AlertService
from app.services.analysis_service import ANALYSIS_VERSION, AnalysisService
from app.services.market.models import MarketContext


class StaticMarketProvider:
    """In-memory market provider that returns a canned context."""
    name = "stub"
    def get_context(self, *, symbol, exchange):
        return MarketContext(
            symbol=symbol, exchange=exchange,
            current_price=25000.0, day_high=25100.0, day_low=24900.0,
            previous_close=24950.0, volume=1_000_000,
            market_status="OPEN", source="stub",
        )


def _wire(db_session: Session) -> AlertService:
    repo = AlertRepository(db_session)
    analysis = AnalysisService(
        market=StaticMarketProvider(),
        ai=MockAIProvider(),
        prompt_builder=PromptBuilder(),
        validator=JsonValidator(),
    )
    return AlertService(repo=repo, analysis=analysis)


def test_ingest_stores_alert_with_cto_approved_metadata(db_session: Session) -> None:
    svc = _wire(db_session)
    parsed = TradingViewAlertIn(
        symbol=" nifty ", exchange=" nse ", signal="buy",
        price=25000.0, timeframe="15m", strategy="EMA Breakout",
    )
    a = svc.ingest_tradingview(
        raw_payload={"symbol": " nifty ", "signal": "buy", "extra": "kept"},
        parsed=parsed,
    )
    # v0.2 stable
    assert a.symbol == "NIFTY"
    assert a.signal == "BUY"
    assert a.status == "analyzed"
    assert a.analysis["recommendation"] == "BUY"
    assert a.analysis["confidence"] == 74
    assert a.raw_payload["extra"] == "kept"

    # v0.3 CTO-approved names
    assert a.ai_provider == "mock"
    assert a.ai_model == "mock-1"
    assert a.ai_prompt and "Signal:     BUY" in a.ai_prompt
    assert a.ai_response and '"recommendation": "BUY"' in a.ai_response
    assert a.analysis_latency_ms is not None and a.analysis_latency_ms >= 1
    assert a.analysis_version == ANALYSIS_VERSION
    assert a.prompt_version  # non-empty
    assert a.market_context is not None
    assert a.market_context["current_price"] == 25000.0


def test_get_by_id_missing_raises(db_session: Session) -> None:
    svc = _wire(db_session)
    with pytest.raises(AlertNotFoundError):
        svc.get_by_id(9999)


def test_delete_removes_alert(db_session: Session) -> None:
    svc = _wire(db_session)
    parsed = TradingViewAlertIn(symbol="X", exchange="NSE", signal="BUY", price=1.0)
    a = svc.ingest_tradingview(raw_payload={"x": 1}, parsed=parsed)
    svc.delete(a.id)
    with pytest.raises(AlertNotFoundError):
        svc.get_by_id(a.id)


def test_statistics_counts_by_signal(db_session: Session) -> None:
    svc = _wire(db_session)
    for sig, price in (("BUY", 1.0), ("BUY", 2.0), ("SELL", 3.0)):
        svc.ingest_tradingview(
            raw_payload={"signal": sig},
            parsed=TradingViewAlertIn(
                symbol="X", exchange="NSE", signal=sig, price=price  # type: ignore[arg-type]
            ),
        )
    stats = svc.statistics()
    assert stats.total_alerts == 3
    assert stats.buy_alerts == 2
    assert stats.sell_alerts == 1
    assert stats.latest_alert is not None
    assert stats.latest_alert.signal == "SELL"
