"""Pydantic schemas for the Alert resource.

Wire shapes for the ingest and read endpoints, plus the analysis payload
returned by AI providers. Kept separate from the ORM model so persistence
and API can evolve independently.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Analysis payload — produced by AIProvider.analyze, stored on Alert.analysis
# ---------------------------------------------------------------------------


class AlertAnalysis(BaseModel):
    """Structured output of an AI provider for a single alert."""

    recommendation: Literal["BUY", "SELL", "HOLD"] = Field(
        ..., description="Directional recommendation."
    )
    confidence: int = Field(
        ..., ge=0, le=100, description="Confidence score, 0–100."
    )
    risk: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ..., description="Categorical risk rating."
    )
    reasoning: list[str] = Field(
        default_factory=list,
        description="Ordered list of one-liner justifications.",
    )
    provider: str = Field(
        default="mock",
        description="Name of the AIProvider that generated this analysis.",
    )


# ---------------------------------------------------------------------------
# Inbound TradingView webhook payload
# ---------------------------------------------------------------------------


class TradingViewAlertIn(BaseModel):
    """Inbound TradingView webhook payload.

    Required: ``symbol``, ``exchange``, ``signal``, ``price``.
    Optional fields cover the free-form parts of TradingView's alert template.
    Unknown extra fields are allowed and preserved in the stored raw payload.
    """

    symbol: str = Field(..., min_length=1, max_length=50)
    exchange: str = Field(..., min_length=1, max_length=20)
    signal: Literal["BUY", "SELL"]
    price: float = Field(..., gt=0, description="Reference price. Must be > 0.")
    timeframe: Optional[str] = Field(default=None, max_length=20)
    strategy: Optional[str] = Field(default=None, max_length=100)
    timestamp: Optional[datetime] = Field(
        default=None, description="Timestamp reported by TradingView."
    )

    model_config = ConfigDict(extra="allow")

    @field_validator("symbol", mode="before")
    @classmethod
    def _normalise_symbol(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("exchange", mode="before")
    @classmethod
    def _normalise_exchange(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("signal", mode="before")
    @classmethod
    def _normalise_signal(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value


# ---------------------------------------------------------------------------
# Outbound alert representations
# ---------------------------------------------------------------------------


AlertStatus = Literal["pending", "analyzed", "notified", "archived"]


class AlertOut(BaseModel):
    """Full outbound representation of a stored alert."""

    id: int
    source: str
    symbol: str
    exchange: str
    signal: str
    timeframe: Optional[str] = None
    strategy: Optional[str] = None
    price: float
    alert_timestamp: Optional[datetime] = None
    raw_payload: dict[str, Any]
    analysis: Optional[AlertAnalysis] = None
    status: AlertStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertCreated(BaseModel):
    """Response payload for the webhook ingest endpoint.

    Includes the mock/real AI analysis so callers see the pipeline result
    without needing an additional GET.
    """

    id: int = Field(..., description="Identifier of the newly-stored alert.")
    status: AlertStatus = Field(..., description="Lifecycle status after ingest.")
    created_at: datetime = Field(..., description="UTC ingest timestamp.")
    analysis: AlertAnalysis = Field(..., description="AI analysis generated at ingest.")


class AlertListOut(BaseModel):
    """Paginated list of alerts."""

    items: list[AlertOut]
    total: int = Field(..., description="Total matching rows (unfiltered by paging).")
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Row offset used for this response.")


class StatisticsOut(BaseModel):
    """Summary statistics for the ingest pipeline."""

    total_alerts: int
    buy_alerts: int
    sell_alerts: int
    latest_alert: Optional[AlertOut] = None
    application_version: str
    build: str
    codename: str
