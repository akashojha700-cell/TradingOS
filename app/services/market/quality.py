"""Deterministic Trade Quality Score (F015).

Before the LLM is called, TradingOS scores the setup 0–100 purely from the
computed indicators + the risk-engine reward:risk. This is deterministic (same
facts → same score), so it can gate/rank trades without the model and is passed
into the prompt as one more grounded fact for the LLM to weigh.

Scoring (direction-aware, max 100):
    EMA alignment matches signal ............ +20
    RSI in the favourable zone .............. +15
    Volume above average (ratio > 1.0) ...... +15
    MACD histogram in the signal direction .. +20
    ADX > 25 (trending, not chopping) ....... +15
    Reward:risk > 2.0 ....................... +15
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.services.market.models import MarketContext


@dataclass(frozen=True)
class QualityScore:
    """A deterministic 0–100 setup score with a human-readable breakdown."""

    score: int
    breakdown: list[str] = field(default_factory=list)

    def to_prompt_line(self) -> str:
        detail = "; ".join(self.breakdown) if self.breakdown else "no confirming factors"
        return f"{self.score}/100 ({detail})"


def compute_quality_score(
    *,
    signal: str,
    context: MarketContext,
    reward_risk: Optional[float] = None,
) -> QualityScore:
    """Return a deterministic setup score for a BUY/SELL signal."""
    sig = (signal or "").strip().upper()
    score = 0
    breakdown: list[str] = []

    want_trend = "BULLISH" if sig == "BUY" else "BEARISH" if sig == "SELL" else None

    # 1) EMA alignment / trend matches the signal direction (+20)
    if want_trend is not None and context.trend == want_trend:
        score += 20
        breakdown.append("EMA/trend aligned +20")

    # 2) RSI in the favourable zone (+15)
    if context.rsi14 is not None:
        if sig == "BUY" and 50.0 <= context.rsi14 <= 70.0:
            score += 15
            breakdown.append("RSI 50-70 +15")
        elif sig == "SELL" and 30.0 <= context.rsi14 <= 50.0:
            score += 15
            breakdown.append("RSI 30-50 +15")

    # 3) Volume above average (+15)
    if context.volume_ratio is not None and context.volume_ratio > 1.0:
        score += 15
        breakdown.append("volume above avg +15")

    # 4) MACD histogram in the signal direction (+20)
    if context.macd_hist is not None:
        if (sig == "BUY" and context.macd_hist > 0) or (sig == "SELL" and context.macd_hist < 0):
            score += 20
            breakdown.append("MACD in direction +20")

    # 5) ADX > 25 → trending market (+15)
    if context.adx is not None and context.adx > 25.0:
        score += 15
        breakdown.append("ADX>25 trending +15")

    # 6) Reward:risk > 2.0 (+15)
    if reward_risk is not None and reward_risk > 2.0:
        score += 15
        breakdown.append("reward:risk>2 +15")

    return QualityScore(score=min(100, score), breakdown=breakdown)
