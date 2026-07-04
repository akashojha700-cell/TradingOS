"""Application-wide constants.

Single source of truth for static values that would otherwise be duplicated
across the codebase. Environment-driven, tunable values live in
``app/config/settings.py``.
"""

from __future__ import annotations

from app.version import BUILD, CODENAME, VERSION

# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

APP_NAME: str = "TradingOS"

APP_DESCRIPTION: str = (
    "TradingOS — an AI-powered Trading Operating System for Indian F&O. "
    "Provider-agnostic, free-first, modular monolith."
)

APP_BANNER: str = f"{APP_NAME} {VERSION} — {CODENAME} ({BUILD})"

# ---------------------------------------------------------------------------
# URL prefixes
# ---------------------------------------------------------------------------

#: Prefix applied to all business (non-system) endpoints.
API_V1_PREFIX: str = "/api/v1"

# ---------------------------------------------------------------------------
# OpenAPI tag labels
# ---------------------------------------------------------------------------

TAG_SYSTEM: str = "system"
TAG_WEBHOOKS: str = "webhooks"
TAG_ALERTS: str = "alerts"
TAG_STATISTICS: str = "statistics"

# ---------------------------------------------------------------------------
# Source labels for ingested data
# ---------------------------------------------------------------------------

SOURCE_TRADINGVIEW: str = "tradingview"

# ---------------------------------------------------------------------------
# HTTP headers
# ---------------------------------------------------------------------------

HEADER_WEBHOOK_SECRET: str = "X-Webhook-Secret"
HEADER_REQUEST_ID: str = "X-Request-ID"

__all__ = [
    "APP_NAME",
    "APP_DESCRIPTION",
    "APP_BANNER",
    "API_V1_PREFIX",
    "TAG_SYSTEM",
    "TAG_WEBHOOKS",
    "TAG_ALERTS",
    "TAG_STATISTICS",
    "SOURCE_TRADINGVIEW",
    "HEADER_WEBHOOK_SECRET",
    "HEADER_REQUEST_ID",
    "VERSION",
    "BUILD",
    "CODENAME",
]
