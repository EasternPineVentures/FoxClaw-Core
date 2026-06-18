"""Forecast receipt builder and neutral-engine bridge."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from foxclaw import __version__
from foxclaw.engine import gate, score

from .contracts import EvidenceDossier, ForecastReceipt
from .policy import assess_event_contract_policy
from .resolution import assess_resolution_quality

_ZERO = Decimal("0")
_ONE = Decimal("1")


def assess_forecast(
    *,
    market: Any,
    dossier: EvidenceDossier,
    independent_probability: Decimal | str,
    minimum_usable_edge: Decimal | str = Decimal("0.05"),
    spread_cost: Decimal | str = Decimal("0"),
    venue_fee_cost: Decimal | str = Decimal("0"),
    modeled_slippage: Decimal | str = Decimal("0"),
    uncertainty_haircut: Decimal | str = Decimal("0"),
    legal_or_eligibility_penalty: Decimal | str = Decimal("0"),
) -> ForecastReceipt:
    """Run market + dossier + independent probability through the neutral gate."""

    p_yes = _prob(independent_probability, "independent_probability")
    min_edge = _nonnegative(minimum_usable_edge, "minimum_usable_edge")
    costs_total = sum(
        (
            _nonnegative(spread_cost, "spread_cost"),
            _nonnegative(venue_fee_cost, "venue_fee_cost"),
            _nonnegative(modeled_slippage, "modeled_slippage"),
            _nonnegative(uncertainty_haircut, "uncertainty_haircut"),
            _nonnegative(legal_or_eligibility_penalty, "legal_or_eligibility_penalty"),
        ),
        _ZERO,
    )

    yes_ask = _optional_prob(getattr(market, "yes_ask", None), "yes_ask")
    no_ask = _optional_prob(getattr(market, "no_ask", None), "no_ask")
    yes_edge = (p_yes - yes_ask - costs_total) if yes_ask is not None else None
    no_edge = ((_ONE - p_yes) - no_ask - costs_total) if no_ask is not None else None
    side, market_probability, edge = _select_side(yes_edge=yes_edge, no_edge=no_edge,
                                                  yes_ask=yes_ask, no_ask=no_ask)

    resolution_quality = assess_resolution_quality(market)
    policy = assess_event_contract_policy(
        market_id=getattr(market, "market_id"),
        dossier=dossier,
        resolution_quality=resolution_quality,
    )

    sample_size = max(0, dossier.independence_group_count)
    quality = float(dossier.evidence_quality)
    composite = score.composite_score(quality, 1.0, sample_size)
    tier = score.decision_tier(composite, sample_size, mean_reward=quality - 0.5)
    record = {
        "decision": tier,
        "score": composite,
        "trades": sample_size,
        "trust_tier": score.trust_tier(sample_size),
    }
    raw_commitment = float(max(_ZERO, edge or _ZERO))
    gate_verdict = gate.evaluate(
        f"forecast:{getattr(market, 'market_id')}:{side}",
        raw_commitment,
        record,
    )

    verdict, reason = _verdict(
        policy_ok=policy.can_enter_paper,
        side=side,
        edge=edge,
        min_edge=min_edge,
        adjusted_commitment=Decimal(str(gate_verdict.adjusted_commitment)),
        policy_reasons=policy.reasons,
    )
    return ForecastReceipt(
        market_id=getattr(market, "market_id"),
        side=side,
        verdict=verdict,
        independent_probability=p_yes,
        market_probability=market_probability,
        costs_total=costs_total,
        usable_edge=max(_ZERO, edge or _ZERO),
        minimum_usable_edge=min_edge,
        evidence_quality=dossier.evidence_quality,
        dossier_hash=dossier.dossier_hash,
        engine_subject=gate_verdict.subject,
        engine_tier=gate_verdict.tier,
        gate_multiplier=Decimal(str(gate_verdict.multiplier)),
        raw_commitment=Decimal(str(gate_verdict.raw_commitment)),
        adjusted_commitment=Decimal(str(gate_verdict.adjusted_commitment)),
        reason=reason,
        code_version=__version__,
        created_at=datetime.now(UTC).replace(microsecond=0),
    )


def build_forecast_scoreboard(event_outcomes: list[Any]) -> dict[str, Any]:
    """Build a resolved forecast scoreboard with market-baseline comparison."""

    from .calibration import brier_score

    rows = [_row(item) for item in event_outcomes]
    resolved = [row for row in rows if row["resolved"]]
    if not resolved:
        return {
            "resolved_forecasts": 0,
            "brier_score": None,
            "market_brier_score": None,
            "net_paper_result": "0",
            "by_category": {},
        }
    probs = [row["forecast_probability"] for row in resolved]
    market_probs = [row["market_probability"] for row in resolved]
    outcomes = [row["outcome_yes"] for row in resolved]
    by_category: dict[str, dict[str, Any]] = {}
    for row in resolved:
        cat = row["category"]
        bucket = by_category.setdefault(cat, {"resolved": 0, "net_paper_result": Decimal("0")})
        bucket["resolved"] += 1
        bucket["net_paper_result"] += row["net_result"]
    return {
        "resolved_forecasts": len(resolved),
        "brier_score": format(brier_score(probs, outcomes), "f"),
        "market_brier_score": format(brier_score(market_probs, outcomes), "f"),
        "net_paper_result": format(sum((row["net_result"] for row in resolved), Decimal("0")), "f"),
        "by_category": {
            key: {
                "resolved": value["resolved"],
                "net_paper_result": format(value["net_paper_result"], "f"),
            }
            for key, value in sorted(by_category.items())
        },
    }


def _row(item: Any) -> dict[str, Any]:
    get = item.get if isinstance(item, dict) else lambda key, default=None: getattr(item, key, default)
    outcome = get("outcome_yes", get("resolved_outcome") == "yes")
    return {
        "resolved": bool(get("resolved", True)),
        "category": str(get("category", "uncategorized")),
        "forecast_probability": _decimal(get("forecast_probability", get("independent_probability")), "forecast_probability"),
        "market_probability": _decimal(get("market_probability"), "market_probability"),
        "outcome_yes": bool(outcome),
        "net_result": _decimal(get("net_result", "0"), "net_result"),
    }


def _select_side(
    *,
    yes_edge: Decimal | None,
    no_edge: Decimal | None,
    yes_ask: Decimal | None,
    no_ask: Decimal | None,
) -> tuple[str, Decimal | None, Decimal | None]:
    candidates: list[tuple[str, Decimal, Decimal]] = []
    if yes_edge is not None and yes_ask is not None:
        candidates.append(("yes", yes_ask, yes_edge))
    if no_edge is not None and no_ask is not None:
        candidates.append(("no", no_ask, no_edge))
    if not candidates:
        return "none", None, None
    side, price, edge = max(candidates, key=lambda item: item[2])
    if edge <= _ZERO:
        return "none", price, edge
    return side, price, edge


def _verdict(
    *,
    policy_ok: bool,
    side: str,
    edge: Decimal | None,
    min_edge: Decimal,
    adjusted_commitment: Decimal,
    policy_reasons: tuple[str, ...],
) -> tuple[str, str]:
    if not policy_ok:
        return "reject", ",".join(policy_reasons)
    if side == "none" or edge is None or edge <= _ZERO:
        return "reject", "no_positive_usable_edge"
    if edge < min_edge:
        return "watch", "positive_edge_below_minimum"
    if adjusted_commitment <= _ZERO:
        return "reject", "neutral_gate_blocked"
    return "paper", "paper_candidate"


def _prob(value: Decimal | str, label: str) -> Decimal:
    dec = _decimal(value, label)
    if dec < _ZERO or dec > _ONE:
        raise ValueError(f"{label} must be in [0, 1]")
    return dec


def _optional_prob(value: Any, label: str) -> Decimal | None:
    if value is None:
        return None
    return _prob(value, label)


def _nonnegative(value: Decimal | str, label: str) -> Decimal:
    dec = _decimal(value, label)
    if dec < _ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return dec


def _decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"{label} must be Decimal or fixed-point string")
    if isinstance(value, Decimal):
        dec = value
    elif isinstance(value, str):
        try:
            dec = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"{label} is not a valid Decimal") from exc
    else:
        raise TypeError(f"{label} must be Decimal or fixed-point string")
    if not dec.is_finite():
        raise ValueError(f"{label} must be finite")
    return dec
