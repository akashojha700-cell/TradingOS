"""MarketDataProvider protocol + factory.

Providers are stateless — a single instance is created at DI time and reused
per request. Failure to fetch data is *not* an exception at the boundary; the
provider returns a :class:`MarketContext` with ``error`` populated and
whatever fields it managed to gather.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from app.config import Settings
from app.services.market.models import MarketContext


@runtime_checkable
class MarketDataProvider(Protocol):
    """Contract every market data provider fulfils."""

    name: str

    def get_context(
        self, *, symbol: str, exchange: str, timeframe: Optional[str] = None
    ) -> MarketContext:
        """Return a :class:`MarketContext` snapshot for the given symbol."""
        ...


def get_market_provider(settings: Settings) -> "MarketDataProvider":
    """Return the configured market data provider (Yahoo Finance by default)."""
    # Only one provider today; future work: FMP, Alpha Vantage, broker feeds.
    from app.services.market.yahoo import YahooMarketProvider
    return YahooMarketProvider()
