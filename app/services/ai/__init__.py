"""AI provider package.

Exposes the :class:`AIProvider` interface, the concrete implementations, and
the factory. Also re-exports the prompt builder + JSON validator so callers
can construct the pipeline via one import.
"""

from app.services.ai.base import AIProvider
from app.services.ai.factory import get_ai_provider
from app.services.ai.json_validator import JsonValidator
from app.services.ai.mock import MockAIProvider
from app.services.ai.ollama import OllamaProvider, OllamaProviderError
from app.services.ai.prompt_builder import PROMPT_VERSION, PromptBuilder, SYSTEM_INSTRUCTION
from app.services.ai.schemas import ProviderResponse

__all__ = [
    "AIProvider",
    "MockAIProvider",
    "OllamaProvider",
    "OllamaProviderError",
    "get_ai_provider",
    "JsonValidator",
    "PromptBuilder",
    "PROMPT_VERSION",
    "SYSTEM_INSTRUCTION",
    "ProviderResponse",
]
