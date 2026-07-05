"""Yahoo Finance market data provider (via yfinance).

Fetches recent candles for the signal's timeframe and computes an objective set
of indicators (via :mod:`app.services.market.indicators`) that the AI then
interprets. It never uses ``fast_info`` — that path raises ``currentTradingPeriod``
on indices — only the robust ``history()`` call, with a daily fallback when
intraday data is unavailable (e.g. market closed).

Deliberately defensive: any yfinance failure MUST NOT crash the ingest
pipeline. On failure it returns a :class:`MarketContext` with ``error``
populated so downstream layers still proceed with a partial context.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.core.logging import get_logger
from app.services.market.indicators import compute_indicators
from app.services.market.models import MarketContext

logger = get_logger("tradingos.market.yahoo")


_INDEX_MAP: dict[str, str] = {
    "NIFTY":      "^NSEI",
    "NIFTY50":    "^NSEI",
    "BANKNIFTY":  "^NSEBANK",
    "FINNIFTY":   "^CNXFIN",
    "SENSEX":     "^BSESN",
    "MIDCPNIFTY": "^NSEMDCP50",
}

_EXCHANGE_SUFFIX: dict[str, str] = {
    "NSE": ".NS",
    "BSE": ".BO",
    "MCX": ".NS",  # commodity fallback (imperfect; yfinance MCX is spotty)
}

# TradingView timeframe -> (yfinance interval, yfinance period).
# yfinance caps: 1m ≤ 7d, ≤30m ≤ 60d, 1h ≤ 730d. We request enough candles to
# seed EMA200 where possible, and fall back to daily for long lookbacks.
_TIMEFRAME_MAP: dict[str, tuple[str, str]] = {
    "1m":  ("1m",  "5d"),
    "3m":  ("5m",  "1mo"),   # yfinance has no native 3m; 5m is the closest
    "5m":  ("5m",  "1mo"),
    "15m": ("15m", "1mo"),
    "30m": ("30m", "2mo"),
    "45m": ("30m", "2mo"),
    "1h":  ("60m", "3mo"),
    "60m": ("60m", "3mo"),
    "2h":  ("60m", "3mo"),
    "1d":  ("1d",  "1y"),
    "day": ("1d",  "1y"),
    "1w":  ("1wk", "5y"),
}
_DEFAULT_INTERVAL_PERIOD: tuple[str, str] = ("15m", "1mo")
_DAILY_FALLBACK: tuple[str, str] = ("1d", "1y")


def _resolve_ticker(symbol: str, exchange: str) -> str:
    """Return the Yahoo ticker for a TradingOS symbol/exchange pair."""
    sym = (symbol or "").strip().upper()
    exch = (exchange or "").strip().upper()
    if sym in _INDEX_MAP:
        return _INDEX_MAP[sym]
    if sym.startswith("^") or "." in sym:
        return sym  # caller passed a Yahoo ticker directly
    return sym + _EXCHANGE_SUFFIX.get(exch, ".NS")


def _interval_period(timeframe: Optional[str]) -> tuple[str, str]:
    key = (timeframe or "").strip().lower()
    return _TIMEFRAME_MAP.get(key, _DEFAULT_INTERVAL_PERIOD)


def _is_market_open_ist() -> str:
    """Rough Indian F&O market-hours check (09:15–15:30 IST, Mon–Fri)."""
    now_utc = datetime.now(timezone.utc)
    minute_of_day = ((now_utc.hour * 60) + now_utc.minute + (5 * 60 + 30)) % (24 * 60)
    day = now_utc.weekday()  # 0 = Monday
    if day >= 5:
        return "CLOSED"
    return "OPEN" if 555 <= minute_of_day <= 930 else "CLOSED"


class YahooMarketProvider:
    """OHLCV history → computed indicators via yfinance."""

    name: str = "yahoo"

    def get_context(
        self, *, symbol: str, exchange: str, timeframe: Optional[str] = None
    ) -> MarketContext:
        """Return a market snapshot with computed indicators. Never raises."""
        ticker_id = _resolve_ticker(symbol, exchange)
        interval, period = _interval_period(timeframe)
        base = MarketContext(
            symbol=symbol.strip().upper(),
            exchange=exchange.strip().upper(),
            timeframe=timeframe,
            market_status=_is_market_open_ist(),  # type: ignore[arg-type]
            source="yahoo",
        )

        try:
            import yfinance as yf  # lazy import — tests don't need yfinance
        except Exception as exc:  # pragma: no cover - only when dep missing
            logger.warning("market.yfinance.import_failed", error=str(exc))
            base.error = f"yfinance unavailable: {exc}"
            return base

        df = self._fetch_candles(yf, ticker_id, interval, period)
        if df is None or len(df) == 0:
            base.error = f"no candles for {ticker_id}"
            logger.warning("market.candles.empty", ticker=ticker_id, interval=interval)
            return base

        try:
            ind = compute_indicators(df)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("market.indicators.failed", ticker=ticker_id, error=str(exc))
            base.error = f"indicator compute failed: {exc.__class__.__name__}"
            return base

        for field, value in ind.items():
            if hasattr(base, field) and value is not None:
                setattr(base, field, value)

        logger.info(
            "market.context.fetched",
            ticker=ticker_id, interval=interval, candles=ind.get("candles"),
            trend=ind.get("trend"), rsi=ind.get("rsi14"),
            have_price=ind.get("current_price") is not None,
        )
        return base

    def get_candles(
        self, *, symbol: str, exchange: str,
        timeframe: Optional[str] = None, limit: int = 200,
    ) -> dict:
        """Return recent OHLCV candles for charting. Never raises.

        Shape: ``{"symbol", "timeframe", "interval", "candles": [{time, open,
        high, low, close, volume}], "source", "error"?}`` where ``time`` is a
        UNIX timestamp (seconds) suitable for lightweight-charts.
        """
        ticker_id = _resolve_ticker(symbol, exchange)
        interval, period = _interval_period(timeframe)
        out: dict = {
            "symbol": symbol.strip().upper(), "exchange": exchange.strip().upper(),
            "timeframe": timeframe, "interval": interval, "source": "yahoo",
            "candles": [],
        }
        try:
            import yfinance as yf  # lazy import
        except Exception as exc:  # pragma: no cover
            out["error"] = f"yfinance unavailable: {exc}"
            return out

        df = self._fetch_candles(yf, ticker_id, interval, period)
        if df is None or len(df) == 0:
            out["error"] = f"no candles for {ticker_id}"
            return out

        df = df.tail(max(1, min(int(limit), 1000)))
        candles: list[dict] = []
        for ts, row in df.iterrows():
            try:
                t = int(ts.timestamp())
            except Exception:
                continue
            try:
                candles.append({
                    "time":   t,
                    "open":   round(float(row["Open"]), 2),
                    "high":   round(float(row["High"]), 2),
                    "low":    round(float(row["Low"]), 2),
                    "close":  round(float(row["Close"]), 2),
                    "volume": int(float(row.get("Volume", 0) or 0)),
                })
            except Exception:
                continue
        out["candles"] = candles
        if not candles:
            out["error"] = "no usable candle rows"
        return out

    def _fetch_candles(self, yf, ticker_id: str, interval: str, period: str):
        """Fetch candles for the requested interval; fall back to daily.

        Returns a DataFrame (ascending) or None. Uses ``history()`` only.
        """
        for iv, pr in ((interval, period), _DAILY_FALLBACK):
            try:
                t = yf.Ticker(ticker_id)
                df = t.history(period=pr, interval=iv, auto_adjust=False)
                if df is not None and len(df) > 0:
                    if iv != interval:
                        logger.info(
                            "market.candles.daily_fallback",
                            ticker=ticker_id, wanted=interval, used=iv,
                        )
                    return df
            except Exception as exc:  # pragma: no cover - network / rate-limit
                logger.info(
                    "market.candles.attempt_failed",
                    ticker=ticker_id, interval=iv, error=str(exc),
                )
                continue
        return None
