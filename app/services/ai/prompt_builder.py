"""Prompt builder — the highest-leverage file in TradingOS.

Composes a strict-format instruction for the LLM:

  Role   ── Professional Indian F&O index trader
  Task   ── Analyse the incoming TradingView signal
  Context── Symbol, exchange, signal, price, timeframe, strategy, market snapshot
  Rules  ── Conservative on thin data; never hallucinate stops
  Output ── JSON only, exact keys, no prose

The output schema is versioned via ``PROMPT_VERSION`` so we can compare
prompt-quality across releases.
"""

from __future__ import annotations

from typing import Any, Dict

from app.services.market.models import MarketContext

#: Bump when the prompt shape or schema fields change materially.
#: v5 completes the architectural split: the deterministic risk engine computes
#: the trade plan (entry/stop/targets/size); the LLM only EVALUATES that plan
#: against the market fact sheet — it never invents prices or levels.
PROMPT_VERSION: str = "prompt-v5"

SYSTEM_INSTRUCTION: str = (
    "You are a professional Indian F&O index trader with 15 years of experience. "
    "You are cautious, risk-aware, and hate low-quality setups. "
    "You are given a market fact sheet and a pre-computed trade plan. You do NOT "
    "calculate indicators and you do NOT change the plan's numbers — you evaluate "
    "whether the trade should be executed, judging the setup quality from the "
    "facts. You reply with ONE valid JSON object and nothing else. "
    "No markdown. No code fences. No thinking. No prose before or after the JSON."
)

_JSON_SCHEMA_BLOCK: str = """{
  "recommendation": "BUY" | "SELL" | "HOLD",
  "confidence": 0-100 integer,
  "risk": "LOW" | "MEDIUM" | "HIGH",
  "trade_strength": "WEAK" | "MODERATE" | "STRONG" | "VERY_STRONG",
  "reasoning": ["short bullet", "short bullet", "short bullet"]
}"""

_RULES: str = """Rules:
- Base your judgement ONLY on the market facts (and the computed trade plan, if
  shown) above. Do not invent or estimate any value that is not listed.
- You are evaluating the plan, not creating it. Do NOT output entry, stop-loss,
  targets or position size — those are fixed by the risk engine.
- recommendation reflects your verdict: keep the signal's direction (BUY/SELL) if
  the facts support the plan, or downgrade to HOLD if the setup is weak or the
  facts contradict it.
- If a fact is missing or the snapshot contradicts the signal, be MORE
  conservative, not less.
- confidence >= 70 requires at least one confirming factor in the market context
  (e.g. trend alignment, RSI, MACD, volume ratio, price vs support/resistance).
- reasoning must contain 3-6 short, factual, non-repetitive bullet points that
  justify your verdict with reference to the supplied facts.
- Every field is required. Never omit a field.

Return ONLY valid JSON.
No explanations.
No markdown.
No code fences.
No thinking.
No text before or after the JSON."""


class PromptBuilder:
    """Build the LLM prompt for a single ingest."""

    version: str = PROMPT_VERSION

    def build(
        self, *, alert: Dict[str, Any], market: MarketContext,
        plan: Any = None, quality: Any = None,
    ) -> str:
        """Assemble the full user-prompt string.

        When ``plan`` (a risk-engine ``TradePlan`` with ``to_prompt_block``) is
        supplied, the LLM is asked to *evaluate* that pre-computed plan; without
        it, it falls back to assessing the raw signal against the facts.
        """
        signal_block = (
            f"TradingView signal:\n"
            f"  Symbol:     {alert.get('symbol', '?')}\n"
            f"  Exchange:   {alert.get('exchange', '?')}\n"
            f"  Signal:     {alert.get('signal', '?')}\n"
            f"  Price:      {alert.get('price', '?')}\n"
            f"  Timeframe:  {alert.get('timeframe') or '—'}\n"
            f"  Strategy:   {alert.get('strategy')  or '—'}\n"
            f"  Timestamp:  {alert.get('timestamp') or '—'}"
        )
        market_block = "Market context:\n" + market.to_prompt_block()
        if quality is not None and hasattr(quality, "to_prompt_line"):
            market_block += "\n  Trade quality score  " + quality.to_prompt_line()

        if plan is not None and hasattr(plan, "to_prompt_block"):
            task = (
                "TASK\n"
                "A trade plan has already been computed by the deterministic risk\n"
                "engine from the market facts below. Do NOT change any number.\n"
                "Evaluate whether this trade should be EXECUTED as-is or downgraded\n"
                "to HOLD, and explain your verdict.\n"
            )
            plan_block = "Trade plan (computed — do not modify):\n" + plan.to_prompt_block()
            body = f"{signal_block}\n\n{market_block}\n\n{plan_block}\n\n"
        else:
            task = (
                "TASK\n"
                "Analyse the following Indian F&O signal against the market facts and\n"
                "produce a structured verdict. Output MUST be a single JSON object.\n"
            )
            body = f"{signal_block}\n\n{market_block}\n\n"

        return (
            f"{task}\n"
            f"{body}"
            "JSON SCHEMA (return an object with exactly these keys)\n"
            f"{_JSON_SCHEMA_BLOCK}\n\n"
            f"{_RULES}\n"
        )
