"""Deterministic Trade Quality Score tests."""

from __future__ import annotations

from app.services.market.models import MarketContext
from app.services.market.quality import compute_quality_score


def _ctx(**over):
    d = dict(symbol="NIFTY", exchange="NSE", timeframe="15m")
    d.update(over)
    return MarketContext(**d)


def test_perfect_bullish_setup_scores_100():
    ctx = _ctx(trend="BULLISH", rsi14=60.0, volume_ratio=1.8, macd_hist=15.0, adx=30.0)
    q = compute_quality_score(signal="BUY", context=ctx, reward_risk=2.4)
    assert q.score == 100
    assert len(q.breakdown) == 6


def test_no_confirming_factors_scores_zero():
    ctx = _ctx(trend="BEARISH", rsi14=80.0, volume_ratio=0.5, macd_hist=-5.0, adx=10.0)
    q = compute_quality_score(signal="BUY", context=ctx, reward_risk=1.0)
    assert q.score == 0
    assert q.breakdown == []


def test_partial_setup_is_additive():
    # trend aligned (+20) + RSI zone (+15) only
    ctx = _ctx(trend="BULLISH", rsi14=60.0, volume_ratio=0.9, macd_hist=-1.0, adx=10.0)
    q = compute_quality_score(signal="BUY", context=ctx, reward_risk=1.5)
    assert q.score == 35


def test_sell_direction_awareness():
    ctx = _ctx(trend="BEARISH", rsi14=40.0, volume_ratio=1.5, macd_hist=-8.0, adx=28.0)
    q = compute_quality_score(signal="SELL", context=ctx, reward_risk=2.5)
    assert q.score == 100


def test_score_capped_and_deterministic():
    ctx = _ctx(trend="BULLISH", rsi14=60.0, volume_ratio=2.0, macd_hist=20.0, adx=40.0)
    a = compute_quality_score(signal="BUY", context=ctx, reward_risk=3.0)
    b = compute_quality_score(signal="BUY", context=ctx, reward_risk=3.0)
    assert a.score == b.score == 100
    assert "quality" not in a.to_prompt_line().lower()  # sanity: line renders
    assert a.to_prompt_line().startswith("100/100")
