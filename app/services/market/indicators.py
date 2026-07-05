"""Deterministic technical-indicator engine (F005).

The AI must never calculate indicators — it only *interprets* them. This module
turns a candle DataFrame into an objective set of facts (EMA/RSI/MACD/ATR/VWAP/
volume ratio/support-resistance/trend) using pure pandas/numpy. No network, no
randomness, no LLM — so it is fully deterministic and unit-testable.

Input contract
--------------
``compute_indicators(df)`` expects a time-ascending ``pandas.DataFrame`` with at
least ``High``, ``Low``, ``Close`` columns (``Volume`` optional) and a
``DatetimeIndex``. Every output is ``None`` when there is insufficient data, so
callers can degrade gracefully rather than crash.
"""

from __future__ import annotations

from typing import Any, Optional

try:  # pandas/numpy ship with yfinance; guard so importing never hard-fails.
    import numpy as np
    import pandas as pd
except Exception:  # pragma: no cover - only if the scientific stack is absent
    np = None  # type: ignore[assignment]
    pd = None  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Single-value indicator helpers. Each returns a float (last value) or None.
# --------------------------------------------------------------------------- #


def ema(series: "pd.Series", period: int) -> Optional[float]:
    """Exponential moving average (last value). None if fewer than ``period`` rows."""
    s = series.dropna()
    if len(s) < period:
        return None
    return float(s.ewm(span=period, adjust=False).mean().iloc[-1])


def rsi(series: "pd.Series", period: int = 14) -> Optional[float]:
    """Wilder's RSI (last value), 0–100. None if fewer than ``period + 1`` rows."""
    s = series.dropna()
    if len(s) < period + 1:
        return None
    delta = s.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    last_gain = float(avg_gain.iloc[-1])
    last_loss = float(avg_loss.iloc[-1])
    if last_loss == 0.0:
        return 100.0 if last_gain > 0.0 else 50.0
    rs = last_gain / last_loss
    return float(100.0 - (100.0 / (1.0 + rs)))


def macd(
    series: "pd.Series", fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Return (macd_line, signal_line, histogram) last values, or (None, …)."""
    s = series.dropna()
    if len(s) < slow + signal:
        return None, None, None
    ema_fast = s.ewm(span=fast, adjust=False).mean()
    ema_slow = s.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return (
        float(macd_line.iloc[-1]),
        float(signal_line.iloc[-1]),
        float(hist.iloc[-1]),
    )


def atr(
    high: "pd.Series", low: "pd.Series", close: "pd.Series", period: int = 14
) -> Optional[float]:
    """Wilder's Average True Range (last value). None if insufficient rows."""
    if len(close.dropna()) < period + 1:
        return None
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_series = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    val = atr_series.iloc[-1]
    return None if pd.isna(val) else float(val)


def vwap(df: "pd.DataFrame") -> Optional[float]:
    """Session VWAP over the most recent trading day. None if no usable volume."""
    if "Volume" not in df.columns:
        return None
    day = df
    try:
        # Restrict to the latest calendar day so VWAP is a session figure.
        last_day = df.index[-1].date()
        day = df[df.index.map(lambda ts: ts.date() == last_day)]
    except Exception:
        day = df
    vol = day["Volume"].fillna(0.0)
    if float(vol.sum()) <= 0.0:
        return None
    typical = (day["High"] + day["Low"] + day["Close"]) / 3.0
    return float((typical * vol).sum() / vol.sum())


def volume_ratio(volume: "pd.Series", period: int = 20) -> Optional[float]:
    """Latest volume / average volume over ``period``. None if no usable volume."""
    v = volume.dropna()
    if len(v) < 2:
        return None
    window = v.iloc[-period:] if len(v) >= period else v
    avg = float(window.mean())
    if avg <= 0.0:
        return None
    return round(float(v.iloc[-1]) / avg, 2)


def adx(
    high: "pd.Series", low: "pd.Series", close: "pd.Series", period: int = 14
) -> Optional[float]:
    """Wilder's ADX (last value), 0–100 trend-strength. None if insufficient."""
    if len(close.dropna()) < 2 * period:
        return None
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = ((up_move > down_move) & (up_move > 0)) * up_move
    minus_dm = ((down_move > up_move) & (down_move > 0)) * down_move
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    atr_s = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    atr_s = atr_s.replace(0.0, float("nan"))
    plus_di = 100.0 * (plus_dm.ewm(alpha=1.0 / period, adjust=False).mean() / atr_s)
    minus_di = 100.0 * (minus_dm.ewm(alpha=1.0 / period, adjust=False).mean() / atr_s)
    di_sum = (plus_di + minus_di).replace(0.0, float("nan"))
    dx = 100.0 * (plus_di - minus_di).abs() / di_sum
    val = dx.ewm(alpha=1.0 / period, adjust=False).mean().iloc[-1]
    return None if (val != val) else float(val)  # NaN guard


def bollinger_bands(
    close: "pd.Series", period: int = 20, mult: float = 2.0
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Return (upper, mid, lower) Bollinger Bands (last values), or (None, …)."""
    s = close.dropna()
    if len(s) < period:
        return None, None, None
    mid = s.rolling(period).mean().iloc[-1]
    std = s.rolling(period).std(ddof=0).iloc[-1]
    if mid != mid or std != std:  # NaN guard
        return None, None, None
    return float(mid + mult * std), float(mid), float(mid - mult * std)


def support_resistance(
    high: "pd.Series", low: "pd.Series", lookback: int = 20
) -> tuple[Optional[float], Optional[float]]:
    """Recent swing support/resistance from the last ``lookback`` candles."""
    h = high.dropna()
    l = low.dropna()
    if len(h) < 2 or len(l) < 2:
        return None, None
    resistance = float(h.iloc[-lookback:].max())
    support = float(l.iloc[-lookback:].min())
    return support, resistance


def classify_trend(
    ema20: Optional[float], ema50: Optional[float], ema200: Optional[float]
) -> str:
    """Trend from EMA alignment: BULLISH / BEARISH / NEUTRAL."""
    if ema20 is None or ema50 is None:
        return "NEUTRAL"
    if ema200 is not None:
        if ema20 > ema50 > ema200:
            return "BULLISH"
        if ema20 < ema50 < ema200:
            return "BEARISH"
        return "NEUTRAL"
    if ema20 > ema50:
        return "BULLISH"
    if ema20 < ema50:
        return "BEARISH"
    return "NEUTRAL"


# --------------------------------------------------------------------------- #
# Aggregate
# --------------------------------------------------------------------------- #


def _round(v: Optional[float], nd: int = 2) -> Optional[float]:
    return None if v is None else round(v, nd)


def compute_indicators(df: "pd.DataFrame") -> dict[str, Any]:
    """Compute the full fact set from a candle DataFrame.

    Returns a flat dict of primitive values (floats/str/int or None). Safe on
    empty/short input — every field simply degrades to ``None``.
    """
    empty: dict[str, Any] = {
        "current_price": None, "day_high": None, "day_low": None,
        "previous_close": None, "volume": None,
        "ema20": None, "ema50": None, "ema200": None,
        "rsi14": None, "macd": None, "macd_signal": None, "macd_hist": None,
        "atr14": None, "vwap": None, "volume_ratio": None,
        "adx": None, "bb_upper": None, "bb_mid": None, "bb_lower": None,
        "support": None, "resistance": None, "trend": "NEUTRAL", "candles": 0,
    }
    if pd is None or df is None or len(df) == 0:
        return empty

    df = df.copy()
    # Normalise column names (yfinance uses title-case; be forgiving).
    df.columns = [str(c).title() for c in df.columns]
    for col in ("High", "Low", "Close"):
        if col not in df.columns:
            return empty
    if "Volume" not in df.columns:
        df["Volume"] = 0.0

    close, high, low = df["Close"], df["High"], df["Low"]

    e20 = ema(close, 20)
    e50 = ema(close, 50)
    e200 = ema(close, 200)
    macd_line, macd_sig, macd_hist = macd(close)
    bb_upper, bb_mid, bb_lower = bollinger_bands(close)
    support, resistance = support_resistance(high, low)

    # Price summary from the latest session.
    current = _round(float(close.iloc[-1]))
    try:
        last_day = df.index[-1].date()
        session = df[df.index.map(lambda ts: ts.date() == last_day)]
    except Exception:
        session = df
    day_high = _round(float(session["High"].max()))
    day_low = _round(float(session["Low"].min()))

    # Previous close = last close of the prior session (falls back to prev row).
    previous_close: Optional[float] = None
    try:
        prior = df[df.index.map(lambda ts: ts.date() != last_day)]
        if len(prior) > 0:
            previous_close = _round(float(prior["Close"].iloc[-1]))
    except Exception:
        previous_close = None
    if previous_close is None and len(close) >= 2:
        previous_close = _round(float(close.iloc[-2]))

    last_vol = df["Volume"].iloc[-1]
    volume = int(last_vol) if (last_vol == last_vol and last_vol > 0) else None

    return {
        "current_price": current,
        "day_high": day_high,
        "day_low": day_low,
        "previous_close": previous_close,
        "volume": volume,
        "ema20": _round(e20),
        "ema50": _round(e50),
        "ema200": _round(e200),
        "rsi14": _round(rsi(close), 1),
        "macd": _round(macd_line, 3),
        "macd_signal": _round(macd_sig, 3),
        "macd_hist": _round(macd_hist, 3),
        "atr14": _round(atr(high, low, close)),
        "vwap": _round(vwap(df)),
        "volume_ratio": volume_ratio(df["Volume"]),
        "adx": _round(adx(high, low, close), 1),
        "bb_upper": _round(bb_upper),
        "bb_mid": _round(bb_mid),
        "bb_lower": _round(bb_lower),
        "support": _round(support),
        "resistance": _round(resistance),
        "trend": classify_trend(e20, e50, e200),
        "candles": int(len(df)),
    }
