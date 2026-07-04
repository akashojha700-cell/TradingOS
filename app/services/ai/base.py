"""AI provider interface.

Every AI provider — mock, Ollama, OpenAI, Anthropic, Gemini — implements the
same interface. Callers depend only on the Protocol; the concrete provider is
resolved by :func:`app.services.ai.factory.get_ai_provider` from configuration.

Sprint 1 ships only the deterministic :class:`MockAIProvider`. Real providers
land in later sprints; no service-layer changes required.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.schemas.alert import AlertAnalysis


@runtime_checkable
class AIProvider(Protocol):
    """Contract every AI provider fulfils."""

    #: Stable identifier used in logs and stored on the analysis payload.
    name: str

    def analyze(self, *, alert_data: dict[str, Any]) -> AlertAnalysis:
        """Return an :class:`AlertAnalysis` for the given alert context.

        Args:
            alert_data: Parsed alert fields plus any contextual data assembled
                by the service layer.

        Returns:
            Structured analysis (recommendation, confidence, risk, reasoning).
        """
        ...
