"""Common Pydantic response schemas.

These models describe the responses returned by the foundational system
endpoints (``/``, ``/health``, ``/version``). Keeping them centralised makes
them easy to evolve and to reference from API_SPEC.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    """Payload returned by ``GET /``."""

    name: str = Field(..., description="Application name.")
    version: str = Field(..., description="Application semantic version.")
    environment: str = Field(..., description="Runtime environment.")
    docs_url: str = Field(default="/docs", description="OpenAPI docs URL.")
    message: str = Field(
        default="TradingOS API is running.",
        description="Human-readable status message.",
    )


class HealthResponse(BaseModel):
    """Payload returned by ``GET /health``."""

    status: Literal["ok", "degraded", "error"] = Field(
        ..., description="Overall service status."
    )
    database: Literal["ok", "error"] = Field(
        ..., description="Database connectivity status."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the health check executed.",
    )


class VersionResponse(BaseModel):
    """Payload returned by ``GET /version``."""

    name: str = Field(..., description="Application name.")
    version: str = Field(..., description="Application semantic version.")
    build: str = Field(..., description="Build label (e.g. 'Sprint-1').")
    codename: str = Field(..., description="Release codename.")
    environment: str = Field(..., description="Runtime environment.")
    python: str = Field(..., description="Python runtime version.")
