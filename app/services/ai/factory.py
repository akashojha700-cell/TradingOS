"""Concrete-provider resolver.

Reads configuration and returns the right :class:`AIProvider` implementation.
Sprint 1 always returns :class:`MockAIProvider`; later sprints add branches
for Ollama / OpenAI / Anthropic / Gemini.
"""

from __future__ import annotations

from app.config import Settings
from app.services.ai.base import AIProvider
from app.services.ai.mock import MockAIProvider


def get_ai_provider(settings: Settings) -> AIProvider:
    """Return an :class:`AIProvider` selected from configuration.

    Currently only ``mock`` is available. Later sprints will branch on
    ``settings.ai_provider``.
    """
    # Only one provider today; branch when the second one lands.
    return MockAIProvider()
