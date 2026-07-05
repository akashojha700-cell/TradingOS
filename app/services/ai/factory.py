"""AI provider factory — picks the concrete provider from configuration."""

from __future__ import annotations

from app.config import Settings
from app.services.ai.base import AIProvider
from app.services.ai.mock import MockAIProvider
from app.services.ai.ollama import OllamaProvider


def get_ai_provider(settings: Settings) -> AIProvider:
    """Return the AIProvider selected by ``AI_PROVIDER`` env var.

    Supported values (case-insensitive): ``mock`` (default), ``ollama``.
    Any unknown value falls back to ``mock`` and emits a warning at first use.
    """
    name = (getattr(settings, "ai_provider", "mock") or "mock").strip().lower()

    if name == "ollama":
        return OllamaProvider(
            host=settings.ollama_host,
            model=settings.ollama_model,
            timeout_seconds=float(settings.ollama_timeout_seconds),
        )
    # Default & explicit "mock"
    return MockAIProvider()
