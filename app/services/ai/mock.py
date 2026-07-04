"""Deterministic mock AI provider.

Returns hand-crafted, deterministic responses shaped like the real provider
output. Its purpose is to validate the *pipeline* (ingest → analyze → persist
→ expose) without depending on any external model.

Determinism is important: tests should be able to assert exact analysis
output for a given input.
"""

from __future__ import annotations

from typing import Any

from app.schemas.alert import AlertAnalysis


class MockAIProvider:
    """A deterministic ``AIProvider`` used in Sprint 1 and in test suites."""

    name: str = "mock"

    def analyze(self, *, alert_data: dict[str, Any]) -> AlertAnalysis:
        """Return a fixed analysis shape driven by the alert's ``signal``."""
        signal = str(alert_data.get("signal", "")).upper()
        strategy = alert_data.get("strategy") or "Signal received"
        timeframe = alert_data.get("timeframe") or "unspecified"

        if signal == "BUY":
            return AlertAnalysis(
                recommendation="BUY",
                confidence=74,
                risk="MEDIUM",
                reasoning=[
                    f"{strategy} detected",
                    "Trend is bullish",
                    "Momentum positive",
                    f"Timeframe: {timeframe}",
                ],
                provider=self.name,
            )
        if signal == "SELL":
            return AlertAnalysis(
                recommendation="SELL",
                confidence=68,
                risk="MEDIUM",
                reasoning=[
                    f"{strategy} detected",
                    "Trend is bearish",
                    "Downside momentum forming",
                    f"Timeframe: {timeframe}",
                ],
                provider=self.name,
            )

        # Defensive fallback — should not normally trigger since the ingest
        # schema constrains ``signal`` to BUY / SELL.
        return AlertAnalysis(
            recommendation="HOLD",
            confidence=50,
            risk="LOW",
            reasoning=["No clear directional signal", "Holding position"],
            provider=self.name,
        )
