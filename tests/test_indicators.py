"""Deterministic indicator-engine tests (no network)."""

from __future__ import annotations

import pandas as pd

from app.services.market.indicators import (
    compute_indicators, ema, rsi, classify_trend, volume_ratio, support_resistance,
    adx, bollinger_bands,
)


def _df(closes, highs=None, lows=None, vols=None):
    n = len(closes)
    idx = pd.date_range("2026-01-01 09:15", periods=n, freq="15min")
    highs = highs or [c + 1 for c in closes]
    lows = lows or [c - 1 for c in closes]
    vols = vols or [1000] * n
    return pd.DataFrame(
        {"High": highs, "Low": lows, "Close": closes, "Volume": vols}, index=idx
    )


def test_ema_matches_pandas_reference():
    s = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
    assert ema(s, 5) == float(s.ewm(span=5, adjust=False).mean().iloc[-1])


def test_ema_none_when_insufficient():
    assert ema(pd.Series([1, 2, 3]), 5) is None


def test_rsi_all_gains_is_high():
    s = pd.Series(list(range(1, 40)))  # strictly rising → RSI ~100
    assert rsi(s, 14) > 95


def test_rsi_all_losses_is_low():
    s = pd.Series(list(range(40, 1, -1)))  # strictly falling → RSI ~0
    assert rsi(s, 14) < 5


def test_trend_classification():
    assert classify_trend(110, 100, 90) == "BULLISH"
    assert classify_trend(90, 100, 110) == "BEARISH"
    assert classify_trend(100, 105, 95) == "NEUTRAL"
    assert classify_trend(None, None, None) == "NEUTRAL"


def test_volume_ratio_none_on_zero_volume():
    assert volume_ratio(pd.Series([0, 0, 0, 0])) is None


def test_support_resistance_from_swing():
    sup, res = support_resistance(pd.Series([10, 12, 11, 15, 9]), pd.Series([8, 9, 7, 11, 6]))
    assert res == 15.0 and sup == 6.0


def test_compute_indicators_full_frame():
    closes = [100 + (i * 0.5) for i in range(60)]  # steady uptrend
    ind = compute_indicators(_df(closes))
    assert ind["candles"] == 60
    assert ind["current_price"] == round(closes[-1], 2)
    assert ind["ema20"] is not None and ind["ema50"] is not None
    assert ind["trend"] == "BULLISH"          # rising series → EMA20>EMA50
    assert 0 <= ind["rsi14"] <= 100
    assert ind["support"] is not None and ind["resistance"] is not None


def test_compute_indicators_empty_is_safe():
    ind = compute_indicators(pd.DataFrame())
    assert ind["candles"] == 0 and ind["trend"] == "NEUTRAL" and ind["ema20"] is None
    assert ind["adx"] is None and ind["bb_upper"] is None


def test_adx_none_when_insufficient():
    assert adx(pd.Series([1, 2, 3]), pd.Series([1, 2, 3]), pd.Series([1, 2, 3])) is None


def test_adx_strong_uptrend_is_high():
    closes = [100 + i for i in range(40)]        # steady, strong uptrend
    df = _df(closes)
    val = adx(df["High"], df["Low"], df["Close"], 14)
    assert val is not None and val > 25          # trending market


def test_bollinger_bands_ordering():
    closes = [100 + (i % 5) for i in range(30)]  # oscillating
    up, mid, lo = bollinger_bands(pd.Series(closes), 20, 2.0)
    assert up is not None and up > mid > lo


def test_bollinger_none_when_insufficient():
    assert bollinger_bands(pd.Series([1, 2, 3]), 20)[0] is None


def test_compute_indicators_includes_adx_and_bb():
    closes = [100 + (i * 0.5) for i in range(60)]
    ind = compute_indicators(_df(closes))
    assert ind["adx"] is not None
    assert ind["bb_upper"] is not None and ind["bb_lower"] is not None
    assert ind["bb_upper"] >= ind["bb_mid"] >= ind["bb_lower"]
