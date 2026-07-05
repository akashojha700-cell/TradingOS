"""Deterministic risk-engine tests (no network, no LLM)."""

from __future__ import annotations

from app.services.market.models import MarketContext
from app.services.market.risk_engine import compute_trade_plan


def _ctx(**over):
    d = dict(symbol="NIFTY", exchange="NSE", timeframe="15m",
             current_price=25000.0, atr14=200.0)
    d.update(over)
    return MarketContext(**d)


def test_buy_plan_levels_and_direction():
    plan = compute_trade_plan(signal="BUY", context=_ctx())
    assert plan is not None
    # risk_per_unit = 1.5 * 200 = 300
    assert plan.risk_per_unit == 300.0
    assert plan.entry == 25000.0
    assert plan.stop_loss == 24700.0            # entry - 300
    assert plan.target_1 == 25450.0             # entry + 1.5*300
    assert plan.target_2 == 25900.0             # entry + 3.0*300
    assert plan.reward_risk == 1.5              # 450 / 300
    assert plan.holding_period == "Intraday"
    assert 0.5 <= plan.position_size_percent <= 5.0


def test_sell_plan_is_inverted():
    plan = compute_trade_plan(signal="SELL", context=_ctx())
    assert plan is not None
    assert plan.stop_loss == 25300.0            # entry + 300
    assert plan.target_1 == 24550.0             # entry - 450
    assert plan.target_2 == 24100.0             # entry - 900
    assert plan.stop_loss > plan.entry > plan.target_1


def test_none_without_atr():
    assert compute_trade_plan(signal="BUY", context=_ctx(atr14=None)) is None


def test_none_without_price():
    assert compute_trade_plan(signal="BUY", context=_ctx(current_price=None)) is None


def test_none_for_non_directional_signal():
    assert compute_trade_plan(signal="HOLD", context=_ctx()) is None


def test_holding_period_swing_for_daily():
    plan = compute_trade_plan(signal="BUY", context=_ctx(timeframe="1d"))
    assert plan is not None and plan.holding_period == "Swing"


def test_position_size_is_bounded():
    # Very tight ATR → fixed-fractional sizing gets capped, not unbounded.
    plan = compute_trade_plan(signal="BUY", context=_ctx(atr14=5.0))
    assert plan is not None and plan.position_size_percent <= 5.0


def test_deterministic_repeatable():
    a = compute_trade_plan(signal="BUY", context=_ctx())
    b = compute_trade_plan(signal="BUY", context=_ctx())
    assert a == b
