"""AI provider interface — one primitive: ``generate(prompt) -> ProviderResponse``.

Providers do *not* build prompts and do *not* validate JSON. The prompt is
built by :class:`app.services.ai.prompt_builder.PromptBuilder`; the response
is parsed by :class:`app.services.ai.json_validator.JsonValidator`. This keeps
each layer replaceable — a new provider just implements ``generate()``.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from app.services.ai.schemas import ProviderResponse


@runtime_checkable
class AIProvider(Protocol):
    """Contract every AI provider fulfils."""

    name: str
    model: str

    def generate(self, prompt: str, *, system: Optional[str] = None) -> ProviderResponse:
        """Send a prompt to the model and return the raw response + metadata."""
        ...
