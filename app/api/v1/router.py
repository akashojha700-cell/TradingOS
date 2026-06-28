"""Aggregate router for API v1.

Combines all v1 sub-routers behind a single ``api_router`` that the FastAPI
application mounts at the appropriate prefix.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import alerts, health, root, version, webhooks

api_router = APIRouter()

# Foundational system endpoints (Sprint 0)
api_router.include_router(root.router)
api_router.include_router(health.router)
api_router.include_router(version.router)

# Market event ingestion (Sprint 1)
api_router.include_router(webhooks.router)
api_router.include_router(alerts.router)
