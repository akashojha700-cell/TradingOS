"""Unit tests for :class:`MockAIProvider` under the v0.3 ``generate()`` API."""

from __future__ import annotations

import json

from app.services.ai import MockAIProvider


def _mk_prompt(signal="BUY", strategy="EMA Breakout", timeframe="15m", price=25000.0):
    return (
        "TradingView signal:\n"
        f"  Symbol:     NIFTY\n"
        f"  Exchange:   NSE\n"
        f"  Signal:     {signal}\n"
        f"  Price:      {price}\n"
        f"  Timeframe:  {timeframe}\n"
        f"  Strategy:   {strategy}\n"
    )


def test_mock_generate_returns_provider_response() -> None:
    p = MockAIProvider()
    r = p.generate(_mk_prompt("BUY"))
    assert r.provider == "mock"
    assert r.model == "mock-1"
    assert r.latency_ms >= 1
    assert r.text.startswith("{")


def test_mock_generate_buy_json_shape() -> None:
    p = MockAIProvider()
    body = json.loads(p.generate(_mk_prompt("BUY", strategy="RSI Bull")).text)
    assert body["recommendation"] == "BUY"
    assert body["confidence"] == 74
    assert body["risk"] == "MEDIUM"
    assert body["decision"] == "EXECUTE"
    assert body["provider"] == "mock"
    assert body["position_size_percent"] >= 0
    assert body["reward_risk"] >= 1
    assert isinstance(body["reasoning"], list) and len(body["reasoning"]) >= 2


def test_mock_generate_sell_json_shape() -> None:
    p = MockAIProvider()
    body = json.loads(p.generate(_mk_prompt("SELL")).text)
    assert body["recommendation"] == "SELL"
    assert body["confidence"] == 68
    assert body["risk"] == "MEDIUM"


def test_mock_generate_hold_fallback_on_unknown_signal() -> None:
    p = MockAIProvider()
    # No BUY/SELL in prompt -> mock defaults to HOLD/WAIT
    body = json.loads(p.generate("no signal keyword here").text)
    assert body["recommendation"] == "HOLD"
    assert body["decision"] == "WAIT"
