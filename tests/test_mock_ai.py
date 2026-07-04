"""Unit tests for :class:`MockAIProvider`."""

from __future__ import annotations

from app.services.ai import MockAIProvider


def test_mock_returns_buy_recommendation_for_buy_signal() -> None:
    provider = MockAIProvider()
    result = provider.analyze(
        alert_data={"signal": "BUY", "strategy": "EMA Breakout", "timeframe": "5m"}
    )
    assert result.recommendation == "BUY"
    assert result.confidence == 74
    assert result.risk == "MEDIUM"
    assert result.provider == "mock"
    assert any("EMA Breakout" in line for line in result.reasoning)
    assert any("bullish" in line.lower() for line in result.reasoning)


def test_mock_returns_sell_recommendation_for_sell_signal() -> None:
    provider = MockAIProvider()
    result = provider.analyze(alert_data={"signal": "SELL"})
    assert result.recommendation == "SELL"
    assert result.confidence == 68
    assert any("bearish" in line.lower() for line in result.reasoning)


def test_mock_is_deterministic() -> None:
    provider = MockAIProvider()
    payload = {"signal": "BUY", "strategy": "X", "timeframe": "15m"}
    assert provider.analyze(alert_data=payload) == provider.analyze(alert_data=payload)


def test_mock_falls_back_to_hold_for_unknown_signal() -> None:
    provider = MockAIProvider()
    result = provider.analyze(alert_data={"signal": "HOLD"})
    assert result.recommendation == "HOLD"
