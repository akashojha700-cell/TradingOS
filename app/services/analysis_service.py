"""Analysis service — orchestrates market → prompt → LLM → validate."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

from app.core.logging import get_logger
from app.schemas.alert import AlertAnalysis, TradingViewAlertIn
from app.services.ai import (
    AIProvider,
    JsonValidator,
    PROMPT_VERSION,
    PromptBuilder,
    SYSTEM_INSTRUCTION,
)
from app.services.ai.ollama import OllamaProviderError
from app.services.market import MarketContext, MarketDataProvider
from app.services.market.risk_engine import compute_trade_plan
from app.services.market.quality import compute_quality_score

logger = get_logger("tradingos.analysis")

#: Bumped when the end-to-end analysis flow changes materially.
ANALYSIS_VERSION: str = "v0.3"


@dataclass(frozen=True)
class AnalysisResult:
    """Everything the alert repository needs after the pipeline runs."""

    analysis: AlertAnalysis
    market_context: MarketContext
    prompt: str
    raw_response: str
    latency_ms: int
    model: str
    provider: str
    token_count: Optional[int]
    analysis_version: str
    prompt_version: str


class AnalysisService:
    """High-level pipeline: fetch → prompt → analyze → validate."""

    def __init__(
        self,
        *,
        market: MarketDataProvider,
        ai: AIProvider,
        prompt_builder: PromptBuilder,
        validator: JsonValidator,
    ) -> None:
        self._market = market
        self._ai = ai
        self._prompt = prompt_builder
        self._validator = validator

    def analyze(self, parsed: TradingViewAlertIn) -> AnalysisResult:
        # 1. Market context (never raises)
        try:
            context = self._market.get_context(
                symbol=parsed.symbol, exchange=parsed.exchange, timeframe=parsed.timeframe
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("analysis.market.error", error=str(exc))
            context = MarketContext(
                symbol=parsed.symbol, exchange=parsed.exchange,
                market_status="UNKNOWN",  # type: ignore[arg-type]
                error=f"market provider raised: {exc.__class__.__name__}",
            )

        # 2. Prompt
        alert_dict: dict[str, Any] = {
            "symbol":    parsed.symbol,
            "exchange":  parsed.exchange,
            "signal":    parsed.signal,
            "price":     parsed.price,
            "timeframe": parsed.timeframe,
            "strategy":  parsed.strategy,
            "timestamp": parsed.timestamp.isoformat() if parsed.timestamp else None,
        }
        # 2b. Deterministic risk engine — compute the trade plan BEFORE the LLM.
        # The LLM will evaluate this plan, not invent one. None when data is thin.
        plan = compute_trade_plan(signal=parsed.signal, context=context)

        # 2c. Deterministic setup score (0-100) — fed to the LLM as a fact and
        # persisted so trades can be ranked/gated without the model.
        quality = compute_quality_score(
            signal=parsed.signal, context=context,
            reward_risk=plan.reward_risk if plan else None,
        )
        prompt = self._prompt.build(
            alert=alert_dict, market=context, plan=plan, quality=quality
        )

        # 3. LLM
        t0 = time.monotonic()
        try:
            response = self._ai.generate(prompt, system=SYSTEM_INSTRUCTION)
            raw_text = response.text
            model_id = response.model
            provider = response.provider
            latency  = response.latency_ms
            tokens   = response.token_count
            logger.info(
                "analysis.llm.ok",
                provider=provider, model=model_id, ms=latency, tokens=tokens,
                prompt_version=self._prompt.version,
            )
        except OllamaProviderError as exc:
            latency = int((time.monotonic() - t0) * 1000)
            logger.warning("analysis.llm.provider_error", error=str(exc), ms=latency)
            raw_text = ""
            model_id = getattr(self._ai, "model", "unknown")
            provider = getattr(self._ai, "name", "unknown")
            tokens = None

        # 4. Validate
        # DIAGNOSTIC: exactly what reaches the validator (covers the empty /
        # timeout path where the provider never logged its own input).
        logger.info(
            "analysis.validator_input",
            provider=provider,
            length=len(raw_text or ""),
            preview=(raw_text or "")[:500],
        )
        analysis = self._validator.parse(raw_text, provider=provider)

        # 4a. Deterministic setup score is authoritative (never from the LLM).
        analysis = analysis.model_copy(update={"quality_score": quality.score})

        # 4b. The trade plan is deterministic: override the LLM's numeric fields
        # with the risk engine's authoritative values. The LLM keeps ownership of
        # recommendation / confidence / risk / trade_strength / reasoning only.
        if plan is not None:
            analysis = analysis.model_copy(update={
                "entry":                   plan.entry,
                "stop_loss":               plan.stop_loss,
                "target_1":                plan.target_1,
                "target":                  plan.target_1,  # legacy alias
                "target_2":                plan.target_2,
                "reward_risk":             plan.reward_risk,
                "position_size_percent":   plan.position_size_percent,
                "suggested_position_size": plan.position_size_percent,
                "holding_period":          plan.holding_period,
            })
            logger.info(
                "analysis.risk_plan_applied",
                entry=plan.entry, stop_loss=plan.stop_loss,
                target_1=plan.target_1, target_2=plan.target_2,
                reward_risk=plan.reward_risk, position_size=plan.position_size_percent,
            )

        if analysis.confidence == 0 and analysis.recommendation == "HOLD":
            logger.warning(
                "analysis.fallback_used",
                provider=provider, model=model_id,
                raw_len=len(raw_text or ""),
                hint="LLM returned no recoverable JSON — check ai.ollama.raw_response above.",
            )

        return AnalysisResult(
            analysis=analysis,
            market_context=context,
            prompt=prompt,
            raw_response=raw_text,
            latency_ms=latency,
            model=model_id,
            provider=provider,
            token_count=tokens,
            analysis_version=ANALYSIS_VERSION,
            prompt_version=self._prompt.version if hasattr(self._prompt, "version") else PROMPT_VERSION,
        )
