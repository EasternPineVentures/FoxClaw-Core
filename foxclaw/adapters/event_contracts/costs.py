"""Versioned cost receipts for event-contract paper simulation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

_ZERO = Decimal("0")
_CENT = Decimal("0.0001")


@dataclass(frozen=True)
class CostReceipt:
    version: str
    spread_cost: Decimal
    venue_fee_cost: Decimal
    modeled_slippage: Decimal
    capital_lock_cost: Decimal

    @property
    def total(self) -> Decimal:
        return self.spread_cost + self.venue_fee_cost + self.modeled_slippage + self.capital_lock_cost


def cost_receipt(
    *,
    spread_cost: Decimal = _ZERO,
    venue_fee_cost: Decimal = _ZERO,
    modeled_slippage: Decimal = _ZERO,
    capital_lock_cost: Decimal = _ZERO,
    version: str = "forecast_cost_model_v1",
) -> CostReceipt:
    values = {
        "spread_cost": spread_cost,
        "venue_fee_cost": venue_fee_cost,
        "modeled_slippage": modeled_slippage,
        "capital_lock_cost": capital_lock_cost,
    }
    for label, value in values.items():
        if value < _ZERO or not value.is_finite():
            raise ValueError(f"{label} must be finite and nonnegative")
    return CostReceipt(
        version=version,
        spread_cost=_q(spread_cost),
        venue_fee_cost=_q(venue_fee_cost),
        modeled_slippage=_q(modeled_slippage),
        capital_lock_cost=_q(capital_lock_cost),
    )


def _q(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)
