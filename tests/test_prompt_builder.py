"""Prompt builder tests."""

from __future__ import annotations

from app.services.ai import PromptBuilder
from app.services.market.models import MarketContext


def _ctx(**over):
    d = dict(symbol="NIFTY", exchange="NSE",
             current_price=25000.0, day_high=25100.0, day_low=24900.0,
             previous_close=24950.0, volume=1_000_000, market_status="OPEN")
    d.update(over)
    return MarketContext(**d)


def test_prompt_contains_signal_and_market_and_schema() -> None:
    pb = PromptBuilder()
    p = pb.build(
        alert={"symbol": "NIFTY", "exchange": "NSE", "signal": "BUY",
               "price": 25000.0, "timeframe": "15m", "strategy": "EMA X",
               "timestamp": "2026-07-04T10:15:00Z"},
        market=_ctx(),
    )
    # Signal / instruction sections
    assert "Signal:     BUY" in p
    assert "Symbol:     NIFTY" in p
    assert "Strategy:   EMA X" in p
    # Market context injected
    assert "Current price" in p and "25000.00" in p
    assert "Previous close" in p and "24950.00" in p
    # Evaluator schema keys present (prompt-v5 — LLM judges, does not price)
    for k in ("recommendation", "confidence", "risk", "trade_strength", "reasoning"):
        assert k in p
    # Strict JSON-only guardrails present
    assert "Return ONLY valid JSON" in p
    assert "No code fences" in p


def test_prompt_handles_partial_market_context() -> None:
    pb = PromptBuilder()
    p = pb.build(
        alert={"symbol": "X", "exchange": "NSE", "signal": "SELL",
               "price": 10.0, "timeframe": None, "strategy": None, "timestamp": None},
        market=_ctx(current_price=None, day_high=None, day_low=None,
                    previous_close=None, volume=None, error="fetch failed"),
    )
    assert "Signal:     SELL" in p
    # Missing numeric fields are simply omitted; error surfaces in the source line
    assert "Current price" not in p
    assert "fetch failed" in p
