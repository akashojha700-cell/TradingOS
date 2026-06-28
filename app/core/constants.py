"""Application-wide constants.

Single source of truth for static values that would otherwise be duplicated
across the codebase — the product name, the OpenAPI description, default tag
labels, source labels for ingested data, and so on.

Environment-driven, tunable values stay in ``app/config/settings.py``. The
distinction:

* **Constants** — same in every environment, change only with a code release.
* **Settings**  — tunable per environment via env vars.
"""

from __future__ import annotations

from app.version import BUILD, CODENAME, VERSION

# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

#: Product name. Used in titles, banners, log fields, and OpenAPI metadata.
APP_NAME: str = "TradingOS"

#: One-paragraph description used in OpenAPI / docs landing.
APP_DESCRIPTION: str = (
    "TradingOS — an AI-powered Trading Operating System for Indian F&O. "
    "Provider-agnostic, free-first, modular monolith."
)

#: Compact banner string emitted at startup and surfaced by ``/version``.
APP_BANNER: str = f"{APP_NAME} {VERSION} — {CODENAME} ({BUILD})"

# ---------------------------------------------------------------------------
# OpenAPI tag labels
# ---------------------------------------------------------------------------

TAG_SYSTEM: str = "system"
TAG_WEBHOOKS: str = "webhooks"
TAG_ALERTS: str = "alerts"

# ---------------------------------------------------------------------------
# Source labels for ingested data
# ---------------------------------------------------------------------------

#: Source identifier persisted on Alert rows ingested from TradingView.
SOURCE_TRADINGVIEW: str = "tradingview"

# ---------------------------------------------------------------------------
# HTTP headers
# ---------------------------------------------------------------------------

#: Header used to convey a shared secret on inbound webhooks.
HEADER_WEBHOOK_SECRET: str = "X-Webhook-Secret"

#: Correlation ID header propagated by RequestIDMiddleware.
HEADER_REQUEST_ID: str = "X-Request-ID"

__all__ = [
    "APP_NAME",
    "APP_DESCRIPTION",
    "APP_BANNER",
    "TAG_SYSTEM",
    "TAG_WEBHOOKS",
    "TAG_ALERTS",
    "SOURCE_TRADINGVIEW",
    "HEADER_WEBHOOK_SECRET",
    "HEADER_REQUEST_ID",
    "VERSION",
    "BUILD",
    "CODENAME",
]
