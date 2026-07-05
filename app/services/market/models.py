"""Pydantic models describing market context passed into the LLM prompt."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class MarketContext(BaseModel):
    """Objective market snapshot + computed indicators for a single symbol.

    Every numeric field is optional because upstream data providers regularly
    fail, rate-limit, or return partial data (Indian indices on Yahoo often
    report zero volume, for example). The prompt builder renders only the
    fields that are present, and the AI is instructed to use ONLY these facts.
    """

    symbol: str = Field(..., description="Symbol the context refers to (normalised upper-case).")
    exchange: str = Field(..., description="Exchange code the caller reported (e.g. NSE).")
    timeframe: Optional[str] = Field(default=None, description="Candle timeframe used (e.g. 15m).")

    # ---- Price summary --------------------------------------------------
    current_price: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    previous_close: Optional[float] = None
    volume: Optional[int] = None

    # ---- Computed indicators (F005) — the AI never calculates these -----
    ema20: Optional[float] = None
    ema50: Optional[float] = None
    ema200: Optional[float] = None
    rsi14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    atr14: Optional[float] = None
    vwap: Optional[float] = None
    volume_ratio: Optional[float] = None
    adx: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_mid: Optional[float] = None
    bb_lower: Optional[float] = None
    support: Optional[float] = None
    resistance: Optional[float] = None
    trend: Literal["BULLISH", "BEARISH", "NEUTRAL"] = "NEUTRAL"
    candles: int = 0

    market_status: Literal["OPEN", "CLOSED", "UNKNOWN"] = "UNKNOWN"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    source: str = "yahoo"
    error: Optional[str] = Field(
        default=None,
        description="Non-null when data could not be fetched. Callers should still proceed.",
    )

    model_config = ConfigDict(extra="ignore")

    @property
    def has_indicators(self) -> bool:
        """True when at least the core trend indicators were computed."""
        return self.ema20 is not None and self.rsi14 is not None

    def to_prompt_block(self) -> str:
        """Human-readable fact sheet for LLM prompt injection.

        Only non-null fields are shown so the model is never handed a blank or
        fabricated value. A leading MACD crossover label is derived from the
        numeric MACD histogram so the model does not have to infer it.
        """
        rows: list[tuple[str, str]] = [
            ("Symbol",        self.symbol),
            ("Exchange",      self.exchange),
        ]
        if self.timeframe:                    rows.append(("Timeframe",       self.timeframe))
        rows.append(("Market status", self.market_status))

        if self.current_price  is not None: rows.append(("Current price",  f"{self.current_price:.2f}"))
        if self.previous_close is not None: rows.append(("Previous close", f"{self.previous_close:.2f}"))
        if self.day_high       is not None: rows.append(("Day high",       f"{self.day_high:.2f}"))
        if self.day_low        is not None: rows.append(("Day low",        f"{self.day_low:.2f}"))
        if self.volume         is not None: rows.append(("Volume",         f"{self.volume:,}"))

        if self.ema20  is not None: rows.append(("EMA20",  f"{self.ema20:.2f}"))
        if self.ema50  is not None: rows.append(("EMA50",  f"{self.ema50:.2f}"))
        if self.ema200 is not None: rows.append(("EMA200", f"{self.ema200:.2f}"))
        rows.append(("Trend", self.trend))

        if self.rsi14 is not None: rows.append(("RSI14", f"{self.rsi14:.1f}"))
        if self.macd_hist is not None:
            cross = "bullish" if self.macd_hist > 0 else "bearish" if self.macd_hist < 0 else "flat"
            rows.append(("MACD histogram", f"{self.macd_hist:.3f} ({cross})"))
        if self.atr14        is not None: rows.append(("ATR14",        f"{self.atr14:.2f}"))
        if self.adx          is not None: rows.append(("ADX14",        f"{self.adx:.1f}"))
        if self.vwap         is not None: rows.append(("VWAP",         f"{self.vwap:.2f}"))
        if self.volume_ratio is not None: rows.append(("Volume ratio", f"{self.volume_ratio:.2f}x avg"))
        if self.bb_upper is not None and self.bb_lower is not None:
            rows.append(("Bollinger", f"{self.bb_lower:.2f} – {self.bb_upper:.2f}"))
        if self.support      is not None: rows.append(("Support",      f"{self.support:.2f}"))
        if self.resistance   is not None: rows.append(("Resistance",   f"{self.resistance:.2f}"))
        if self.candles:                  rows.append(("Candles used", str(self.candles)))

        rows.append(("Data source", f"{self.source}{' (partial: ' + self.error + ')' if self.error else ''}"))
        rows.append(("As of",       self.timestamp.isoformat(timespec="seconds")))

        width = max(len(k) for k, _ in rows) + 1
        return "\n".join(f"  {k.ljust(width)} {v}" for k, v in rows)
