"""Market-side tradeability snapshots for readiness scoring."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketTradeabilityInput:
    liquidity: int
    spread_quality: int
    slippage_risk: int
    timing_quality: int
    entry_quality: int


@dataclass(frozen=True)
class MarketTradeabilitySnapshot:
    tradeability: int
    entry_quality: int
    status: str
    reason_codes: tuple[str, ...]


def build_tradeability_snapshot(values: MarketTradeabilityInput) -> MarketTradeabilitySnapshot:
    """Convert market conditions into readiness inputs."""
    liquidity = _score(values.liquidity)
    spread_quality = _score(values.spread_quality)
    slippage_risk = _score(values.slippage_risk)
    timing_quality = _score(values.timing_quality)
    entry_quality = _score(values.entry_quality)
    tradeability = round(
        liquidity * 0.30
        + spread_quality * 0.25
        + (100 - slippage_risk) * 0.20
        + timing_quality * 0.25
    )
    reasons: list[str] = []
    if liquidity < 45:
        reasons.append("thin_liquidity")
    if spread_quality < 45:
        reasons.append("wide_spread")
    if slippage_risk > 60:
        reasons.append("high_slippage_risk")
    if timing_quality < 45:
        reasons.append("poor_timing")
    if entry_quality < 45:
        reasons.append("poor_entry_quality")
    return MarketTradeabilitySnapshot(
        tradeability=tradeability,
        entry_quality=entry_quality,
        status=_status(min(tradeability, entry_quality)),
        reason_codes=tuple(reasons) or ("tradeability_measured",),
    )


def _status(value: int) -> str:
    if value >= 70:
        return "strong"
    if value >= 45:
        return "acceptable"
    return "poor"


def _score(value: int | float) -> int:
    return max(0, min(100, round(float(value))))
