"""Aggregate router for API v1.

Layout:

* ``/``                  — the HTML SPA (web UI).
* ``/health``, ``/version`` — system endpoints (infrastructure surfaces).
* ``/docs``, ``/openapi.json`` — FastAPI's built-in developer surfaces.
* ``/api/v1/*``          — all business endpoints (info, webhook, alerts,
                           statistics).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    alerts, chat, health, market, root, statistics, version, web, webhooks,
)
from app.core.constants import API_V1_PREFIX

# ---- Root: HTML SPA -----------------------------------------------------
web_router = APIRouter()
web_router.include_router(web.router)

# ---- Infrastructure surfaces at root -----------------------------------
system_router = APIRouter()
system_router.include_router(health.router)
system_router.include_router(version.router)

# ---- Business endpoints under /api/v1 ----------------------------------
business_router = APIRouter(prefix=API_V1_PREFIX)
business_router.include_router(root.router)  # /api/v1/info (JSON banner)
business_router.include_router(webhooks.router)
business_router.include_router(alerts.router)
business_router.include_router(statistics.router)
business_router.include_router(market.router)
business_router.include_router(chat.router)

api_router = APIRouter()
api_router.include_router(web_router)
api_router.include_router(system_router)
api_router.include_router(business_router)
