"""Market data endpoints for the trading workstation (read-only, no side effects).

* ``GET /api/v1/market/context``  — computed MarketContext (indicators) for a
  symbol/timeframe, WITHOUT creating an alert. Powers the market-context panel
  and the multi-timeframe view.
* ``GET /api/v1/market/candles``  — recent OHLCV candles for the chart.

These wrap the existing market provider; they add no new infrastructure and do
not touch the alert/recommendation flow.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.api.dependencies import MarketProviderDep
from app.core.logging import get_logger

router = APIRouter(prefix="/market", tags=["market"])
logger = get_logger("tradingos.api.market")


@router.get("/context", summary="Computed market context (indicators) for a symbol")
def market_context(
    market: MarketProviderDep,
    symbol: str = Query(..., min_length=1, max_length=50),
    exchange: str = Query("NSE", min_length=1, max_length=20),
    timeframe: str = Query("15m", max_length=20),
) -> dict[str, Any]:
    """Return the MarketContext (price + indicators) as JSON. Never raises."""
    ctx = market.get_context(symbol=symbol, exchange=exchange, timeframe=timeframe)
    return ctx.model_dump(mode="json")


@router.get("/candles", summary="Recent OHLCV candles for charting")
def market_candles(
    market: MarketProviderDep,
    symbol: str = Query(..., min_length=1, max_length=50),
    exchange: str = Query("NSE", min_length=1, max_length=20),
    timeframe: str = Query("15m", max_length=20),
    limit: int = Query(200, ge=10, le=1000),
) -> dict[str, Any]:
    """Return candles for the chart. Falls back to an empty list on any failure."""
    fn = getattr(market, "get_candles", None)
    if fn is None:
        return {"symbol": symbol.upper(), "candles": [], "error": "provider has no candles"}
    return fn(symbol=symbol, exchange=exchange, timeframe=timeframe, limit=limit)
