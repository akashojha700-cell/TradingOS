"""Pydantic schemas for the Alert resource.

v0.3 additions are exposed under CTO-approved names:
``ai_provider``, ``ai_model``, ``ai_prompt``, ``ai_response``,
``analysis_latency_ms``, ``analysis_version``, ``prompt_version``,
``market_context``, ``token_count``. All optional, backwards-compatible.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Analysis payload (stored on Alert.analysis JSON column)
# ---------------------------------------------------------------------------


class AlertAnalysis(BaseModel):
    """Structured analysis for a single alert."""

    recommendation: Literal["BUY", "SELL", "HOLD"] = Field(...)
    confidence: int = Field(..., ge=0, le=100)
    risk: Literal["LOW", "MEDIUM", "HIGH"] = Field(...)
    reasoning: list[str] = Field(default_factory=list)
    provider: str = Field(default="mock")

    # v0.3 recommendation-engine fields (aligned with the strict prompt schema).
    # Kept as a permissive str + defaulted float so a partial model response
    # never triggers a HOLD fallback; JsonValidator normalises the values.
    trade_strength: str = Field(default="MODERATE")
    suggested_position_size: float = Field(default=0.0, ge=0.0, le=100.0)

    # F007 trade plan — the model derives these from the supplied fact sheet
    # (current price / ATR / support / resistance). All optional so a partial
    # response never triggers a fallback.
    entry: Optional[float] = Field(default=None)
    target_1: Optional[float] = Field(default=None)
    target_2: Optional[float] = Field(default=None)
    holding_period: str = Field(default="Intraday")

    # F015 deterministic setup score (0-100), computed pre-LLM from indicators.
    quality_score: Optional[int] = Field(default=None, ge=0, le=100)

    # Intelligence-layer fields (all optional for backward compat)
    decision: Literal["EXECUTE", "WAIT", "AVOID"] = Field(default="WAIT")
    position_size_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    reward_risk: float = Field(default=1.0, ge=0.0)
    stop_loss: Optional[float] = Field(default=None)
    target: Optional[float] = Field(default=None)
    invalidating_conditions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


# ---------------------------------------------------------------------------
# Inbound TradingView webhook payload (v0.2 stable — unchanged)
# ---------------------------------------------------------------------------


class TradingViewAlertIn(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    exchange: str = Field(..., min_length=1, max_length=20)
    signal: Literal["BUY", "SELL"]
    price: float = Field(..., gt=0)
    timeframe: Optional[str] = Field(default=None, max_length=20)
    strategy: Optional[str] = Field(default=None, max_length=100)
    timestamp: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(extra="allow")

    @field_validator("symbol",   mode="before")
    @classmethod
    def _norm_symbol(cls, v):   return v.strip().upper() if isinstance(v, str) else v

    @field_validator("exchange", mode="before")
    @classmethod
    def _norm_exchange(cls, v): return v.strip().upper() if isinstance(v, str) else v

    @field_validator("signal",   mode="before")
    @classmethod
    def _norm_signal(cls, v):   return v.strip().upper() if isinstance(v, str) else v


# ---------------------------------------------------------------------------
# Outbound representations
# ---------------------------------------------------------------------------


AlertStatus = Literal["pending", "analyzed", "notified", "archived"]


class AlertOut(BaseModel):
    """Full outbound representation of a stored alert."""

    # v0.2 stable ---------------------------------------------------------
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

    # v0.3 intelligence metadata (all optional) --------------------------
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    ai_prompt: Optional[str] = None
    ai_response: Optional[str] = None
    analysis_latency_ms: Optional[int] = None
    analysis_version: Optional[str] = None
    prompt_version: Optional[str] = None
    market_context: Optional[dict[str, Any]] = None
    token_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class AlertCreated(BaseModel):
    """Response payload from the webhook ingest endpoint."""

    # v0.2 stable
    id: int
    status: AlertStatus
    created_at: datetime
    analysis: AlertAnalysis

    # v0.3 (CTO-approved names)
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    analysis_latency_ms: Optional[int] = None
    analysis_version: Optional[str] = None
    prompt_version: Optional[str] = None


class AlertListOut(BaseModel):
    items: list[AlertOut]
    total: int
    limit: int
    offset: int


class StatisticsOut(BaseModel):
    total_alerts: int
    buy_alerts: int
    sell_alerts: int
    latest_alert: Optional[AlertOut] = None
    application_version: str
    build: str
    codename: str
