"""Event-contract pricing — the mispriced-probability doctrine, in code.

This is the small, pure, central piece the whole Forecast Desk turns on (pin P10). FoxClaw
hunts *mispriced probability*, not high-probability events:

    usable_edge =  FoxClaw_probability
                 − market_implied_probability
                 − spread − fees − slippage − legal/account_restrictions

A 95% event at 98¢ is boring; a 62% event at 43¢ may be the edge. By keeping this formula in
tested code (not just prose) the doctrine can't quietly drift into a confidence casino.

Pure standard library. No I/O, no network, no venue calls — it only does arithmetic on
numbers a caller already fetched from public market data (invariant #11). Read-only by nature.
"""

from __future__ import annotations

import math
from typing import Final

# Event-contract prices are quoted in cents on a 0–100 scale (Kalshi: whole cents 1–99).
_CENTS_PER_DOLLAR: Final = 100.0


def _check_probability(value: float, *, label: str) -> float:
    p = float(value)
    if not math.isfinite(p) or not (0.0 <= p <= 1.0):
        raise ValueError(f"{label} must be a probability in [0, 1], got {value!r}")
    return p


def yes_price_to_implied_probability(price_cents: float) -> float:
    """A YES contract's price (in cents, 0–100) → the market-implied probability (0–1).

    43¢ → 0.43. The price of a binary YES contract *is* the market's probability estimate, so
    this is a unit conversion, not a model. Rejects prices outside the 0–100 cent band.
    """
    cents = float(price_cents)
    if not math.isfinite(cents) or not (0.0 <= cents <= _CENTS_PER_DOLLAR):
        raise ValueError(f"price_cents must be in [0, 100], got {price_cents!r}")
    return cents / _CENTS_PER_DOLLAR


def no_price_to_implied_probability(price_cents: float) -> float:
    """A NO contract's price (cents) → the implied probability of the YES outcome.

    NO and YES prices sum to 100¢ in a binary market, so YES probability = 1 − NO_price.
    """
    return 1.0 - yes_price_to_implied_probability(price_cents)


def edge_gap(*, foxclaw_probability: float, market_probability: float) -> float:
    """Raw edge in probability points: how far FoxClaw's estimate sits from the market's.

    Positive → the market underprices YES (FoxClaw is more bullish); negative → it underprices
    NO. This is the *gross* edge, before costs.
    """
    fc = _check_probability(foxclaw_probability, label="foxclaw_probability")
    mkt = _check_probability(market_probability, label="market_probability")
    return fc - mkt


def usable_edge(
    *,
    foxclaw_probability: float,
    market_probability: float,
    spread: float = 0.0,
    fees: float = 0.0,
    slippage: float = 0.0,
    legal_penalty: float = 0.0,
) -> float:
    """The edge that survives costs, signed by the favored side (0.0 if costs eat it).

    Costs (all ≥ 0) shrink the gross gap toward zero without flipping its sign — they make a
    thin edge unusable, they never invent one on the other side. The magnitude is the
    cost-adjusted edge; the sign tells you which side it favors (+ = YES, − = NO). When costs
    exceed the gross gap, there is no usable edge and this returns ``0.0``.
    """
    gap = edge_gap(foxclaw_probability=foxclaw_probability, market_probability=market_probability)
    costs = 0.0
    for name, value in (("spread", spread), ("fees", fees),
                        ("slippage", slippage), ("legal_penalty", legal_penalty)):
        v = float(value)
        if not math.isfinite(v) or v < 0.0:
            raise ValueError(f"{name} must be a non-negative cost, got {value!r}")
        costs += v
    magnitude = abs(gap) - costs
    if magnitude <= 0.0:
        return 0.0
    return math.copysign(magnitude, gap)


def favored_side(gap: float) -> str:
    """Which side an edge gap points to: ``"yes"`` (gap > 0), ``"no"`` (gap < 0), else ``"none"``."""
    if gap > 0.0:
        return "yes"
    if gap < 0.0:
        return "no"
    return "none"
