"""Deterministic mock AI provider.

Implements the :class:`AIProvider` protocol. Given a prompt, produces a
canned JSON string driven by whichever signal keyword ("BUY"/"SELL") appears
in the prompt. Used to keep tests deterministic and to run the pipeline
end-to-end without Ollama.
"""

from __future__ import annotations

import json
import re
import time
from typing import Optional

from app.services.ai.schemas import ProviderResponse

_STRATEGY_RE = re.compile(r"Strategy:\s*([^\n]+)")
_TIMEFRAME_RE = re.compile(r"Timeframe:\s*([^\n]+)")
_SIGNAL_RE   = re.compile(r"Signal:\s*(BUY|SELL|HOLD)", re.IGNORECASE)
_PRICE_RE    = re.compile(r"Price:\s*([-+]?\d+(?:\.\d+)?)")


class MockAIProvider:
    """A deterministic :class:`AIProvider` used in tests and mock deploys."""

    name:  str = "mock"
    model: str = "mock-1"

    def generate(self, prompt: str, *, system: Optional[str] = None) -> ProviderResponse:
        start = time.monotonic()
        signal = "HOLD"
        strategy = "signal received"
        timeframe = "unspecified"
        price: Optional[float] = None

        m = _SIGNAL_RE.search(prompt or "")
        if m: signal = m.group(1).upper()
        m = _STRATEGY_RE.search(prompt or "")
        if m: strategy = (m.group(1).strip() or strategy)
        m = _TIMEFRAME_RE.search(prompt or "")
        if m: timeframe = (m.group(1).strip() or timeframe)
        m = _PRICE_RE.search(prompt or "")
        if m:
            try: price = float(m.group(1))
            except Exception: price = None

        if signal == "BUY":
            body = {
                "recommendation": "BUY",
                "confidence": 74,
                "risk": "MEDIUM",
                "trade_strength": "STRONG",
                "suggested_position_size": 1.5,
                "decision": "EXECUTE",
                "position_size_percent": 1.5,
                "reward_risk": 2.0,
                "entry":     price if price else 0.0,
                "stop_loss": round(price * 0.985, 2) if price else 0.0,
                "target":    round(price * 1.030, 2) if price else 0.0,
                "target_1":  round(price * 1.030, 2) if price else 0.0,
                "target_2":  round(price * 1.050, 2) if price else 0.0,
                "holding_period": "Intraday",
                "reasoning": [
                    f"{strategy} detected",
                    "Trend is bullish",
                    "Momentum positive",
                    f"Timeframe: {timeframe}",
                ],
                "invalidating_conditions": [
                    "Close below the day low",
                    "Loss of momentum on the next candle",
                ],
                "provider": self.name,
            }
        elif signal == "SELL":
            body = {
                "recommendation": "SELL",
                "confidence": 68,
                "risk": "MEDIUM",
                "trade_strength": "MODERATE",
                "suggested_position_size": 1.0,
                "decision": "EXECUTE",
                "position_size_percent": 1.0,
                "reward_risk": 1.8,
                "entry":     price if price else 0.0,
                "stop_loss": round(price * 1.015, 2) if price else 0.0,
                "target":    round(price * 0.970, 2) if price else 0.0,
                "target_1":  round(price * 0.970, 2) if price else 0.0,
                "target_2":  round(price * 0.950, 2) if price else 0.0,
                "holding_period": "Intraday",
                "reasoning": [
                    f"{strategy} detected",
                    "Trend is bearish",
                    "Downside momentum forming",
                    f"Timeframe: {timeframe}",
                ],
                "invalidating_conditions": [
                    "Reclaim of the previous close",
                    "Volume surge against the direction",
                ],
                "provider": self.name,
            }
        else:
            body = {
                "recommendation": "HOLD",
                "confidence": 50,
                "risk": "LOW",
                "trade_strength": "MODERATE",
                "suggested_position_size": 0.0,
                "decision": "WAIT",
                "position_size_percent": 0.0,
                "reward_risk": 1.0,
                "entry":     price if price else 0.0,
                "stop_loss": 0.0,
                "target":    0.0,
                "target_1":  0.0,
                "target_2":  0.0,
                "holding_period": "Intraday",
                "reasoning": ["No clear directional signal", "Holding position"],
                "invalidating_conditions": ["Any confirmed directional break"],
                "provider": self.name,
            }

        latency_ms = max(1, int((time.monotonic() - start) * 1000))
        return ProviderResponse(
            text=json.dumps(body),
            model=self.model,
            latency_ms=latency_ms,
            token_count=len(prompt.split()) if prompt else None,
            provider=self.name,
        )
