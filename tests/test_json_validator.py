"""JSON validator tests — extract, coerce partial output, only fall back
when no JSON is recoverable at all.
"""

from __future__ import annotations

import json

from app.services.ai import JsonValidator


FULL = {
    "recommendation": "BUY",
    "confidence": 72,
    "risk": "MEDIUM",
    "decision": "EXECUTE",
    "position_size_percent": 1.0,
    "reward_risk": 2.0,
    "stop_loss": 24800.0,
    "target": 25400.0,
    "reasoning": ["A", "B"],
    "invalidating_conditions": ["price loses previous close"],
    "provider": "ollama",
}


# ---- extraction paths --------------------------------------------------


def test_parses_bare_json() -> None:
    r = JsonValidator().parse(json.dumps(FULL), provider="ollama")
    assert r.recommendation == "BUY"
    assert r.confidence == 72
    assert r.decision == "EXECUTE"
    assert r.provider == "ollama"


def test_parses_fenced_json() -> None:
    fenced = "```json\n" + json.dumps(FULL) + "\n```"
    r = JsonValidator().parse(fenced, provider="ollama")
    assert r.recommendation == "BUY"


def test_extracts_json_from_prose() -> None:
    prose = "Here is my analysis:\n\n" + json.dumps(FULL) + "\n\nHope this helps."
    r = JsonValidator().parse(prose, provider="ollama")
    assert r.confidence == 72


def test_strips_think_block() -> None:
    txt = "<think>Reasoning that shouldn't leak...</think>\n" + json.dumps(FULL)
    r = JsonValidator().parse(txt, provider="ollama")
    assert r.recommendation == "BUY"


# ---- coercion (never a HOLD/0 fallback when SOME JSON was recoverable) --


def test_missing_optional_fields_get_derived_defaults() -> None:
    partial = json.dumps({"recommendation": "BUY", "confidence": 78, "risk": "LOW"})
    r = JsonValidator().parse(partial, provider="ollama")
    assert r.recommendation == "BUY"
    assert r.confidence == 78
    assert r.risk == "LOW"
    # Decision derived: conf>=70 AND risk!=HIGH → EXECUTE
    assert r.decision == "EXECUTE"
    # Position size derived (>=60 conf, LOW risk boost)
    assert r.position_size_percent > 0
    assert r.reward_risk >= 1.0
    assert len(r.reasoning) >= 1
    assert r.provider == "ollama"


def test_lowercase_recommendation_is_normalized() -> None:
    r = JsonValidator().parse(json.dumps({"recommendation": "buy", "confidence": 65}),
                              provider="ollama")
    assert r.recommendation == "BUY"


def test_confidence_out_of_range_is_clamped() -> None:
    r = JsonValidator().parse(json.dumps({"recommendation": "SELL", "confidence": 200}),
                              provider="ollama")
    assert r.recommendation == "SELL"
    assert r.confidence == 100


def test_string_confidence_is_coerced() -> None:
    r = JsonValidator().parse(json.dumps({"recommendation": "BUY", "confidence": "77"}),
                              provider="ollama")
    assert r.confidence == 77


def test_string_reasoning_becomes_list() -> None:
    r = JsonValidator().parse(
        json.dumps({"recommendation": "BUY", "confidence": 60,
                    "reasoning": "single string reason"}),
        provider="ollama",
    )
    assert r.reasoning == ["single string reason"]


def test_invalid_recommendation_defaults_to_hold_but_keeps_other_fields() -> None:
    r = JsonValidator().parse(
        json.dumps({"recommendation": "MAYBE", "confidence": 55, "risk": "LOW"}),
        provider="ollama",
    )
    # Recovery: unknown recommendation → HOLD, but other fields are preserved
    # and derived — NOT the conservative fallback (which uses HOLD/0/HIGH).
    assert r.recommendation == "HOLD"
    assert r.confidence == 55           # kept, not zeroed
    assert r.risk == "LOW"              # kept, not HIGH
    assert r.decision == "WAIT"         # derived from HOLD
    # This is coerced output, not fallback — reasoning does NOT contain the
    # standard "could not be parsed" message.
    joined = " ".join(r.reasoning).lower()
    assert "could not be parsed" not in joined


def test_thinking_style_response_still_recovers() -> None:
    """qwen3.6-thinking-style: prose + JSON with fenced markdown."""
    txt = (
        "<think>Let me reason about this trade...</think>\n"
        "Here is my analysis:\n"
        "```json\n"
        + json.dumps({
            "recommendation": "sell", "confidence": 68, "risk": "medium",
            "reasoning": ["momentum weakening", "sup broken"],
        })
        + "\n```"
    )
    r = JsonValidator().parse(txt, provider="ollama")
    assert r.recommendation == "SELL"
    assert r.confidence == 68
    assert r.risk == "MEDIUM"
    assert len(r.reasoning) == 2


# ---- strict-schema (manual-test-shaped) response -----------------------


def test_manual_test_shaped_json_maps_to_new_fields() -> None:
    """The exact 7-field shape that succeeded in manual Ollama testing must
    populate trade_strength + suggested_position_size and NOT fall back."""
    raw = json.dumps({
        "recommendation": "SELL",
        "confidence": 75,
        "risk": "HIGH",
        "trade_strength": "MODERATE",
        "suggested_position_size": 1.5,
        "reward_risk": 1.8,
        "reasoning": ["RSI overbought", "Resistance nearby", "Declining volume"],
    })
    r = JsonValidator().parse(raw, provider="ollama")
    assert r.recommendation == "SELL"
    assert r.confidence == 75
    assert r.risk == "HIGH"
    assert r.trade_strength == "MODERATE"
    assert r.suggested_position_size == 1.5
    # legacy field stays synced for backward compat
    assert r.position_size_percent == 1.5
    assert r.reward_risk == 1.8
    assert len(r.reasoning) == 3
    joined = " ".join(r.reasoning).lower()
    assert "could not be parsed" not in joined


def test_trade_strength_derived_when_absent() -> None:
    r = JsonValidator().parse(
        json.dumps({"recommendation": "BUY", "confidence": 82, "risk": "MEDIUM"}),
        provider="ollama",
    )
    assert r.trade_strength == "STRONG"   # 82 -> STRONG
    assert r.suggested_position_size > 0


# ---- true fallback (only when NOTHING is recoverable) -------------------


def test_fallback_only_when_no_json_is_recoverable() -> None:
    r = JsonValidator().parse("not JSON at all — no braces anywhere", provider="ollama")
    assert r.recommendation == "HOLD"
    assert r.confidence == 0
    assert r.risk == "HIGH"
    assert r.decision == "WAIT"
    joined = " ".join(r.reasoning).lower()
    assert "could not be parsed" in joined
