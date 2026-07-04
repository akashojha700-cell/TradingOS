"""AI provider package.

Exposes the :class:`AIProvider` interface, concrete implementations, and the
factory. Services depend only on the interface and the factory — never on a
specific vendor.
"""

from app.services.ai.base import AIProvider
from app.services.ai.factory import get_ai_provider
from app.services.ai.mock import MockAIProvider

__all__ = ["AIProvider", "MockAIProvider", "get_ai_provider"]
