"""Self-funding proof ledger and claim gate."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping


@dataclass(frozen=True)
class SelfFundingReport:
    mode: str
    resolved_positions: int
    consecutive_days: int
    net_economic_profit: Decimal
    operating_costs: Decimal | None
    self_funding_ratio: Decimal | None
    claim_allowed: bool
    claim_level: str
    reasons: tuple[str, ...]


def evaluate_self_funding(
    *,
    mode: str,
    resolved_positions: int,
    consecutive_days: int,
    net_economic_profit: Decimal,
    operating_costs: Decimal | None,
    standard: Mapping[str, Any],
) -> SelfFundingReport:
    reasons: list[str] = []
    min_days = int(standard.get("minimum_consecutive_days", 90))
    min_positions = int(standard.get("minimum_resolved_positions", 250))
    min_ratio = Decimal(str(standard.get("minimum_self_funding_ratio", "1.25")))
    allowed_modes = set(standard.get("allowed_modes", ()))

    ratio: Decimal | None
    if operating_costs is None:
        ratio = None
        reasons.append("missing_operating_cost_receipts")
    elif operating_costs == 0:
        ratio = None
        reasons.append("zero_operating_costs_cannot_verify_self_funding")
    else:
        ratio = net_economic_profit / operating_costs

    if mode not in allowed_modes:
        reasons.append("mode_not_allowed_for_verified_claim")
    if resolved_positions < min_positions:
        reasons.append("insufficient_resolved_positions")
    if consecutive_days < min_days:
        reasons.append("insufficient_consecutive_days")
    if net_economic_profit <= 0:
        reasons.append("nonpositive_net_economic_profit")
    if ratio is not None and ratio < min_ratio:
        reasons.append("self_funding_ratio_below_standard")

    claim_allowed = not reasons
    if claim_allowed:
        level = "self_funding_verified"
    elif mode == "paper":
        level = "self_funding_candidate"
    else:
        level = "not_verified"
    return SelfFundingReport(
        mode=mode,
        resolved_positions=resolved_positions,
        consecutive_days=consecutive_days,
        net_economic_profit=net_economic_profit,
        operating_costs=operating_costs,
        self_funding_ratio=ratio,
        claim_allowed=claim_allowed,
        claim_level=level,
        reasons=tuple(reasons) if reasons else ("standard_met",),
    )
