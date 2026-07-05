"""AI chat endpoint — free-form trading questions grounded in market facts.

``POST /api/v1/chat`` runs the user's question through the configured local LLM
in *text* mode (JSON mode off). When a symbol is supplied, the current computed
MarketContext fact sheet is appended so the model answers from real numbers.

This reuses the existing Ollama provider; it adds no new infrastructure and does
not touch the recommendation flow.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.dependencies import MarketProviderDep, SettingsDep
from app.core.logging import get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger("tradingos.api.chat")

_SYSTEM = (
    "You are TradingOS Assistant, a concise, practical trading helper for Indian "
    "F&O and equities. Answer clearly and briefly. If market facts are provided, "
    "reason ONLY from them and do not invent numbers. You are NOT a SEBI-registered "
    "advisor: educate and analyse, never guarantee outcomes or give assured calls."
)


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    symbol: Optional[str] = Field(default=None, max_length=50)
    exchange: Optional[str] = Field(default="NSE", max_length=20)
    timeframe: Optional[str] = Field(default=None, max_length=20)


class ChatOut(BaseModel):
    answer: str
    model: str
    provider: str
    latency_ms: int


@router.post("", response_model=ChatOut, summary="Ask the AI a trading question")
def chat(payload: ChatIn, settings: SettingsDep, market: MarketProviderDep) -> ChatOut:
    facts = ""
    if payload.symbol:
        try:
            ctx = market.get_context(
                symbol=payload.symbol,
                exchange=payload.exchange or "NSE",
                timeframe=payload.timeframe,
            )
            facts = "\n\nCurrent market facts (use if relevant):\n" + ctx.to_prompt_block()
        except Exception as exc:  # pragma: no cover - never block chat on data
            logger.info("chat.context.failed", error=str(exc))
            facts = ""

    prompt = payload.message.strip() + facts
    provider_name = (getattr(settings, "ai_provider", "mock") or "mock").strip().lower()

    if provider_name == "ollama":
        from app.services.ai.ollama import OllamaProvider, OllamaProviderError

        # Text mode: JSON formatting OFF so answers are natural prose.
        prov = OllamaProvider(
            host=settings.ollama_host,
            model=settings.ollama_model,
            timeout_seconds=float(settings.ollama_timeout_seconds),
            request_json_mode=False,
            disable_reasoning=True,
        )
        try:
            r = prov.generate(prompt, system=_SYSTEM)
            return ChatOut(
                answer=(r.text or "").strip() or "(the model returned no text)",
                model=r.model, provider=r.provider, latency_ms=r.latency_ms,
            )
        except OllamaProviderError as exc:
            logger.warning("chat.ollama.error", error=str(exc))
            return ChatOut(
                answer=f"AI is currently unavailable ({exc}). Check that Ollama is running.",
                model=settings.ollama_model, provider="ollama", latency_ms=0,
            )

    return ChatOut(
        answer=(
            "Chat is running in mock mode. Set AI_PROVIDER=ollama (with Ollama "
            "running) to get real answers.\n\nYou asked: " + payload.message.strip()
        ),
        model="mock-1", provider="mock", latency_ms=1,
    )
