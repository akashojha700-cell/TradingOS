"""Deterministic risk engine (F008).

Computes the trade plan — entry, stop-loss, targets, reward:risk, position size,
holding period — from the objective :class:`MarketContext` produced by the
indicator engine. This is intentionally free of any LLM: given the same market
facts it always returns the same plan, so trades are reproducible and can be
backtested without the model. The LLM's job is only to *evaluate* this plan.

Model
-----
* ``entry``            = current price.
* ``risk_per_unit``    = ``atr_mult`` × ATR (default 1.5× ATR).
* ``stop_loss``        = entry − risk_per_unit for BUY (entry + for SELL).
* ``target_1/2``       = entry ± ``rr1``/``rr2`` × risk_per_unit.
* ``reward_risk``      = (target_1 − entry) / (entry − stop_loss).
* ``position_size``    = fixed-fractional: risk ``capital_risk_pct`` of capital
                          against the stop distance, capped to ``[0.5, 5.0]`` %.
* ``holding_period``   = Intraday for intraday timeframes, else Swing.

Returns ``None`` when there is not enough data (no price or no ATR) so callers
degrade gracefully to the previous behaviour.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

from app.services.market.models import MarketContext

_INTRADAY_TIMEFRAMES: frozenset[str] = frozenset(
    {"1m", "3m", "5m", "15m", "30m", "45m", "1h", "60m", "2h"}
)


@dataclass(frozen=True)
class TradePlan:
    """Deterministic trade plan derived from market facts."""

    entry: float
    stop_loss: float
    target_1: float
    target_2: float
    reward_risk: float
    position_size_percent: float
    holding_period: str
    risk_per_unit: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_prompt_block(self) -> str:
        """Render the computed plan for the LLM to evaluate (not modify)."""
        rows = [
            ("Entry",         f"{self.entry:.2f}"),
            ("Stop loss",     f"{self.stop_loss:.2f}"),
            ("Target 1",      f"{self.target_1:.2f}"),
            ("Target 2",      f"{self.target_2:.2f}"),
            ("Reward:Risk",   f"{self.reward_risk:.2f}"),
            ("Position size", f"{self.position_size_percent:.2f}% of capital"),
            ("Holding",       self.holding_period),
        ]
        width = max(len(k) for k, _ in rows) + 1
        return "\n".join(f"  {k.ljust(width)} {v}" for k, v in rows)


def _holding_for(timeframe: Optional[str]) -> str:
    return "Intraday" if (timeframe or "").strip().lower() in _INTRADAY_TIMEFRAMES else "Swing"


def compute_trade_plan(
    *,
    signal: str,
    context: MarketContext,
    capital_risk_pct: float = 1.0,
    atr_mult: float = 1.5,
    rr1: float = 1.5,
    rr2: float = 3.0,
    size_floor: float = 0.5,
    size_cap: float = 5.0,
) -> Optional[TradePlan]:
    """Compute a deterministic trade plan, or None if data is insufficient."""
    sig = (signal or "").strip().upper()
    if sig not in ("BUY", "SELL"):
        return None

    entry = context.current_price
    atr = context.atr14
    if entry is None or entry <= 0 or atr is None or atr <= 0:
        return None

    risk_per_unit = round(atr_mult * atr, 2)
    if risk_per_unit <= 0:
        return None

    if sig == "BUY":
        stop_loss = entry - risk_per_unit
        target_1 = entry + rr1 * risk_per_unit
        target_2 = entry + rr2 * risk_per_unit
    else:  # SELL
        stop_loss = entry + risk_per_unit
        target_1 = entry - rr1 * risk_per_unit
        target_2 = entry - rr2 * risk_per_unit

    denom = abs(entry - stop_loss)
    reward_risk = round(abs(target_1 - entry) / denom, 2) if denom > 0 else round(rr1, 2)

    # Fixed-fractional sizing: allocate P% of capital so that a move to the stop
    # loses ~capital_risk_pct of capital. Capped for safety.
    stop_distance_pct = (risk_per_unit / entry) * 100.0
    if stop_distance_pct <= 0:
        position_size = size_floor
    else:
        position_size = capital_risk_pct * 100.0 / stop_distance_pct
    position_size = round(min(size_cap, max(size_floor, position_size)), 2)

    return TradePlan(
        entry=round(entry, 2),
        stop_loss=round(stop_loss, 2),
        target_1=round(target_1, 2),
        target_2=round(target_2, 2),
        reward_risk=reward_risk,
        position_size_percent=position_size,
        holding_period=_holding_for(context.timeframe),
        risk_per_unit=risk_per_unit,
    )
