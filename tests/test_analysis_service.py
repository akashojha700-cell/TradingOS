"""AnalysisService: full pipeline uses mock LLM + stub market."""

from __future__ import annotations

from app.schemas.alert import TradingViewAlertIn
from app.services.ai import JsonValidator, MockAIProvider, PromptBuilder
from app.services.analysis_service import ANALYSIS_VERSION, AnalysisService
from app.services.market.models import MarketContext


class StubMarket:
    name = "stub"
    def get_context(self, *, symbol, exchange):
        return MarketContext(
            symbol=symbol, exchange=exchange,
            current_price=25000.0, day_high=25100.0, day_low=24900.0,
            previous_close=24950.0, volume=1_000_000,
            market_status="OPEN", source="stub",
        )


def test_pipeline_returns_valid_result() -> None:
    svc = AnalysisService(
        market=StubMarket(),
        ai=MockAIProvider(),
        prompt_builder=PromptBuilder(),
        validator=JsonValidator(),
    )
    parsed = TradingViewAlertIn(
        symbol="NIFTY", exchange="NSE", signal="BUY",
        price=25000.0, timeframe="15m", strategy="EMA Breakout",
    )
    r = svc.analyze(parsed)
    assert r.analysis.recommendation == "BUY"
    assert r.analysis.confidence == 74
    assert r.analysis.decision == "EXECUTE"
    assert r.market_context.current_price == 25000.0
    assert r.model == "mock-1"
    assert r.provider == "mock"
    assert r.latency_ms >= 1
    assert r.analysis_version == ANALYSIS_VERSION
    assert "recommendation" in r.prompt  # schema block present


class StubMarketWithAtr:
    """Stub whose context has ATR so the risk engine produces a plan."""
    name = "stub"
    def get_context(self, *, symbol, exchange, timeframe=None):
        return MarketContext(
            symbol=symbol, exchange=exchange, timeframe=timeframe,
            current_price=25000.0, atr14=200.0, ema20=24900.0, ema50=24800.0,
            rsi14=60.0, trend="BULLISH", market_status="OPEN", source="stub",
        )


def test_risk_engine_overrides_numeric_plan():
    """When market data supports it, the deterministic plan wins over the LLM."""
    svc = AnalysisService(
        market=StubMarketWithAtr(),
        ai=MockAIProvider(),
        prompt_builder=PromptBuilder(),
        validator=JsonValidator(),
    )
    parsed = TradingViewAlertIn(
        symbol="NIFTY", exchange="NSE", signal="BUY",
        price=25000.0, timeframe="15m", strategy="EMA Breakout",
    )
    a = svc.analyze(parsed).analysis
    # LLM still owns the verdict…
    assert a.recommendation == "BUY"
    # …but the numbers come from the risk engine (entry - 1.5*ATR = 24700).
    assert a.entry == 25000.0
    assert a.stop_loss == 24700.0
    assert a.target_1 == 25450.0
    assert a.target_2 == 25900.0
    assert a.reward_risk == 1.5
    # The computed plan is echoed into the prompt for the LLM to evaluate.
    assert "Trade plan (computed" in svc.analyze(parsed).prompt
