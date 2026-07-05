"""LLM-response JSON validator with graceful partial-recovery.

Pipeline:

1. **Preclean** — strip ``<think>...</think>`` reasoning blocks and Markdown
   code fences.
2. **Extract** — try direct ``json.loads``; then walk the string for the first
   balanced ``{...}`` object that parses (respecting string literals so
   braces inside JSON strings don't confuse the counter); then a greedy
   regex as last resort.
3. **Coerce** — normalize enum-like fields to their canonical values, clamp
   numerics into their allowed ranges, coerce reasoning to a list, and
   fill in safe defaults for anything the model omitted. Missing
   ``decision`` / ``position_size_percent`` / ``reward_risk`` are *derived*
   from the recommendation + confidence + risk the model did provide.
4. **Validate** — Pydantic then always sees a well-shaped dict.
5. **Fallback** — only fires when *no* JSON object can be extracted at all.
   Formatting bugs, missing optionals, and enum casing never cause a
   fallback.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from pydantic import ValidationError

from app.core.logging import get_logger
from app.schemas.alert import AlertAnalysis

logger = get_logger("tradingos.ai.json_validator")

# ``<think>...</think>`` reasoning blocks — qwen3-thinking, deepseek-r1, etc.
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
# Leading fence with optional language tag.
_LEAD_FENCE = re.compile(r"^\s*```(?:json|JSON)?\s*", re.IGNORECASE)
# Trailing fence.
_TRAIL_FENCE = re.compile(r"\s*```\s*$")
# Last-resort greedy JSON block.
_JSON_BLOCK_GREEDY = re.compile(r"\{[\s\S]*\}", re.MULTILINE)

_ALLOWED_RECS       = ("BUY", "SELL", "HOLD")
_ALLOWED_RISKS      = ("LOW", "MEDIUM", "HIGH")
_ALLOWED_DECISIONS  = ("EXECUTE", "WAIT", "AVOID")
_ALLOWED_STRENGTHS  = ("WEAK", "MODERATE", "STRONG", "VERY_STRONG")


class JsonValidator:
    """Parse + validate LLM responses; coerce partial output; never crash."""

    def parse(self, raw_text: str, *, provider: str) -> AlertAnalysis:
        """Return an :class:`AlertAnalysis`. Never raises."""
        data = self._extract_json(raw_text)
        if data is None:
            logger.warning(
                "ai.json.unparseable",
                provider=provider,
                preview=(raw_text or "")[:180],
            )
            return self._fallback(provider, reason="No JSON object could be extracted")

        coerced = _coerce_partial(data, provider=provider)
        try:
            return AlertAnalysis.model_validate(coerced)
        except ValidationError as exc:  # pragma: no cover — coercion should prevent this
            logger.warning(
                "ai.json.coerced_still_invalid",
                provider=provider,
                errors=exc.error_count(),
                first=str(exc.errors()[0].get("msg")) if exc.errors() else None,
            )
            return self._fallback(
                provider,
                reason="Coerced response failed schema validation",
            )

    # ------------------------------------------------------------------ extract
    def _extract_json(self, text: str) -> Optional[dict[str, Any]]:
        """Try progressively harder to extract a JSON object from ``text``."""
        if not text:
            return None
        cleaned = _preclean(text)

        obj = _try_json_loads(cleaned)
        if obj is not None:
            return obj

        obj = _find_first_balanced_object(cleaned)
        if obj is not None:
            return obj

        m = _JSON_BLOCK_GREEDY.search(cleaned)
        if m:
            obj = _try_json_loads(m.group(0))
            if obj is not None:
                return obj

        return None

    # ------------------------------------------------------------------ fallback
    def _fallback(self, provider: str, *, reason: str) -> AlertAnalysis:
        """Conservative fallback — only invoked when no JSON was recoverable."""
        return AlertAnalysis(
            recommendation="HOLD",
            confidence=0,
            risk="HIGH",
            reasoning=[
                "AI response could not be parsed — falling back to conservative default.",
                f"Reason: {reason}.",
                "No trade recommended until analysis can be validated.",
            ],
            provider=provider,
            decision="WAIT",
            position_size_percent=0.0,
            reward_risk=1.0,
            stop_loss=None,
            target=None,
            invalidating_conditions=["Any subsequent parseable analysis"],
        )


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------


def _preclean(text: str) -> str:
    """Remove reasoning blocks and Markdown fences before parsing."""
    text = _THINK_BLOCK.sub("", text)
    text = _LEAD_FENCE.sub("", text.lstrip())
    text = _TRAIL_FENCE.sub("", text.rstrip())
    return text.strip()


def _try_json_loads(candidate: str) -> Optional[dict[str, Any]]:
    """``json.loads(candidate)`` returning None on any failure or non-object."""
    if not candidate:
        return None
    try:
        obj = json.loads(candidate)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _find_first_balanced_object(text: str) -> Optional[dict[str, Any]]:
    """Return the first balanced JSON object in ``text`` that parses successfully.

    Walks the string character by character, respecting string literals and
    backslash escapes so ``{`` / ``}`` inside quoted values don't confuse the
    depth counter.
    """
    n = len(text)
    for i in range(n):
        if text[i] != "{":
            continue

        depth = 0
        in_string = False
        escape = False
        for j in range(i, n):
            c = text[j]
            if in_string:
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == '"':
                    in_string = False
                continue
            if c == '"':
                in_string = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[i : j + 1]
                    obj = _try_json_loads(candidate)
                    if obj is not None:
                        return obj
                    break  # move on to the next opening brace
    return None


# ---------------------------------------------------------------------------
# Coercion — turn a partial / noisy dict into a shape AlertAnalysis accepts.
# ---------------------------------------------------------------------------


def _norm_enum(value: Any, allowed: tuple[str, ...], default: str) -> str:
    """Uppercase-strip a string and snap to ``allowed``; else return ``default``."""
    if isinstance(value, str):
        v = value.strip().upper()
        if v in allowed:
            return v
    return default


def _norm_float(
    value: Any,
    default: Optional[float],
    *,
    lo: Optional[float] = None,
    hi: Optional[float] = None,
) -> Optional[float]:
    """Coerce to float and clamp; on failure return ``default``."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    if f != f:  # NaN
        return default
    if lo is not None:
        f = max(lo, f)
    if hi is not None:
        f = min(hi, f)
    return f


def _norm_int(
    value: Any,
    default: int,
    *,
    lo: Optional[int] = None,
    hi: Optional[int] = None,
) -> int:
    """Coerce to int (rounding floats) and clamp; on failure return ``default``."""
    try:
        i = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    if lo is not None:
        i = max(lo, i)
    if hi is not None:
        i = min(hi, i)
    return i


def _norm_str_list(value: Any) -> list[str]:
    """Coerce a value to a clean list of non-empty strings."""
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _derive_decision(rec: str, conf: int, risk: str) -> str:
    """Fill in a sensible decision when the model omitted it."""
    if rec == "HOLD":
        return "WAIT"
    if conf >= 70 and risk != "HIGH":
        return "EXECUTE"
    if conf >= 50:
        return "WAIT"
    return "AVOID"


def _derive_position_size(conf: int, risk: str) -> float:
    """Fill in a suggested position size (% of capital)."""
    base = 2.0 if conf >= 80 else 1.0 if conf >= 60 else 0.5
    if risk == "HIGH":
        base *= 0.5
    elif risk == "LOW":
        base *= 1.5
    return round(base, 2)


def _derive_reward_risk(risk: str, conf: int) -> float:
    """Fill in a reward:risk ratio derived from risk grade + confidence."""
    base = 3.0 if risk == "LOW" else 1.5 if risk == "HIGH" else 2.0
    return round(max(1.0, base + (conf - 50) / 100.0), 2)


def _derive_strength(conf: int) -> str:
    """Fill in a trade-strength grade from confidence (mirrors the UI scale)."""
    if conf >= 85:
        return "VERY_STRONG"
    if conf >= 70:
        return "STRONG"
    if conf >= 50:
        return "MODERATE"
    return "WEAK"


def _norm_strength(value: Any, conf: int) -> str:
    """Normalise a trade-strength label; derive from confidence if unusable."""
    if isinstance(value, str):
        v = value.strip().upper().replace(" ", "_").replace("-", "_")
        if v in _ALLOWED_STRENGTHS:
            return v
    return _derive_strength(conf)


def _coerce_partial(data: dict[str, Any], *, provider: str) -> dict[str, Any]:
    """Turn a partial / noisy model dict into a shape that validates.

    The rule is: if the model gave us *something* — even one useful field —
    keep it and fill the rest with derived or neutral defaults. HOLD is only
    used when the model itself said HOLD (or when nothing useful was
    provided for the recommendation).
    """
    rec  = _norm_enum(data.get("recommendation"), _ALLOWED_RECS, "HOLD")
    conf = _norm_int(data.get("confidence"), 50, lo=0, hi=100)
    risk = _norm_enum(data.get("risk"), _ALLOWED_RISKS, "MEDIUM")

    decision = _norm_enum(data.get("decision"), _ALLOWED_DECISIONS, "")
    if not decision:
        decision = _derive_decision(rec, conf, risk)

    # Trade strength — new strict-schema field; derive from confidence if absent.
    trade_strength = _norm_strength(data.get("trade_strength"), conf)

    # Position size — accept the strict-schema name (suggested_position_size)
    # OR the legacy name (position_size_percent); derive if neither is usable.
    position_size = _norm_float(
        data.get("suggested_position_size"), None, lo=0.0, hi=100.0
    )
    if position_size is None:
        position_size = _norm_float(
            data.get("position_size_percent"), None, lo=0.0, hi=100.0
        )
    if position_size is None:
        position_size = _derive_position_size(conf, risk)

    reward_risk = _norm_float(data.get("reward_risk"), None, lo=0.0)
    if reward_risk is None or reward_risk < 1.0:
        reward_risk = _derive_reward_risk(risk, conf)

    # F007 trade plan (price levels are pass-through — the model grounds them in
    # the supplied ATR / support / resistance; we never fabricate prices here).
    entry     = _norm_float(data.get("entry"),    None)
    target_1  = _norm_float(data.get("target_1"), None)
    target_2  = _norm_float(data.get("target_2"), None)

    stop_loss = _norm_float(data.get("stop_loss"), None)
    # Back-compat: keep the legacy single ``target`` in sync with target_1.
    target    = _norm_float(data.get("target"), None)
    if target is None:
        target = target_1

    holding_period = data.get("holding_period")
    holding_period = (
        holding_period.strip()
        if isinstance(holding_period, str) and holding_period.strip()
        else "Intraday"
    )

    reasoning = _norm_str_list(data.get("reasoning"))
    if not reasoning:
        reasoning = [f"{rec} @ {conf}% confidence · {risk} risk (from {provider})."]

    invalidating = _norm_str_list(data.get("invalidating_conditions"))

    provider_out = (
        data["provider"]
        if isinstance(data.get("provider"), str) and data["provider"].strip()
        else provider
    )

    return {
        "recommendation":          rec,
        "confidence":              conf,
        "risk":                    risk,
        "reasoning":               reasoning,
        "provider":                provider_out,
        # Strict-schema recommendation-engine fields
        "trade_strength":          trade_strength,
        "suggested_position_size": position_size,
        # F007 trade plan
        "entry":                   entry,
        "target_1":                target_1,
        "target_2":                target_2,
        "holding_period":          holding_period,
        # Legacy intelligence fields (kept synced for backward compat)
        "decision":                decision,
        "position_size_percent":   position_size,
        "reward_risk":             reward_risk,
        "stop_loss":               stop_loss,
        "target":                  target,
        "invalidating_conditions": invalidating,
    }
