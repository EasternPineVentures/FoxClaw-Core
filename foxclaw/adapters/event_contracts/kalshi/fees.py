"""Versioned Kalshi fee model used by paper simulation.

Phase E keeps the default fee rate at zero unless an explicit schedule is supplied. That
prevents the simulator from inventing live venue economics while still recording the fee
model version used for every receipt.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

_CENT = Decimal("0.0001")


@dataclass(frozen=True)
class KalshiFeeSchedule:
    version: str = "kalshi_fee_model_v0_explicit_zero"
    taker_fee_rate: Decimal = Decimal("0")


def estimate_fee(price: Decimal, contracts: Decimal, *, schedule: KalshiFeeSchedule | None = None) -> Decimal:
    schedule = schedule or KalshiFeeSchedule()
    if price < 0 or contracts < 0 or schedule.taker_fee_rate < 0:
        raise ValueError("price, contracts, and fee rate must be nonnegative")
    return (price * contracts * schedule.taker_fee_rate).quantize(_CENT, rounding=ROUND_HALF_UP)
