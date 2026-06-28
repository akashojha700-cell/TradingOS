"""Pydantic schemas for the Alert resource.

These models describe the **wire shape** of alert-related requests and
responses. They are deliberately separate from the ORM model so persistence
and API can evolve independently.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TradingViewAlertIn(BaseModel):
    """Inbound TradingView webhook payload.

    TradingView's alert payloads are user-authored — fields are loosely typed
    and the set of fields varies by user template. We accept a small required
    surface (``ticker``, ``action``) and preserve everything else in the
    stored ``raw_payload``.
    """

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Symbol the alert refers to (case-insensitive on input).",
    )
    action: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Alert action keyword (e.g. 'buy', 'sell', 'alert').",
    )
    price: Optional[float] = Field(
        default=None,
        description="Optional reference price.",
    )
    timeframe: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Optional timeframe identifier (e.g. '5m').",
    )
    strategy: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional strategy name.",
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional free-text message.",
    )

    # Unknown fields are allowed; they are preserved in the raw payload that
    # the service stores alongside the validated subset.
    model_config = ConfigDict(extra="allow")

    @field_validator("ticker")
    @classmethod
    def _normalise_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("action")
    @classmethod
    def _normalise_action(cls, value: str) -> str:
        return value.strip().lower()


class AlertOut(BaseModel):
    """Outbound representation of a stored alert."""

    id: int
    source: str
    ticker: str
    action: str
    price: Optional[float] = None
    timeframe: Optional[str] = None
    strategy: Optional[str] = None
    message: Optional[str] = None
    received_at: datetime
    raw_payload: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class AlertCreated(BaseModel):
    """Response payload returned from the webhook ingest endpoint."""

    id: int = Field(..., description="Identifier of the newly-stored alert.")
    received_at: datetime = Field(..., description="UTC ingest timestamp.")
    status: str = Field(default="accepted", description="Ingest status marker.")


class AlertListOut(BaseModel):
    """Paginated list of alerts."""

    items: list[AlertOut]
    total: int = Field(..., description="Total matching rows (unfiltered by paging).")
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Row offset used for this response.")
