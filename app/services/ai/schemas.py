"""Shared schemas for the AI subsystem.

Kept separate from :mod:`app.schemas.alert` so the AI layer can evolve its
provider-level shapes (LLM response, timing, tokens) without touching the
public API schema.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderResponse(BaseModel):
    """Raw generation output from an :class:`AIProvider`."""

    text: str = Field(..., description="Raw text produced by the LLM.")
    model: str = Field(..., description="Model identifier the provider used.")
    latency_ms: int = Field(..., ge=0, description="Wall-clock latency in ms.")
    token_count: Optional[int] = Field(
        default=None,
        description="Sum of prompt + completion tokens if the provider reports it.",
    )
    provider: str = Field(..., description="Provider name (e.g. mock / ollama).")

    model_config = ConfigDict(extra="ignore")
