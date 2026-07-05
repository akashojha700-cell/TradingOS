"""Market data package.

Exposes the :class:`MarketDataProvider` protocol and a factory that returns
the configured concrete implementation (Yahoo by default).
"""

from app.services.market.models import MarketContext
from app.services.market.provider import MarketDataProvider, get_market_provider

__all__ = ["MarketContext", "MarketDataProvider", "get_market_provider"]
