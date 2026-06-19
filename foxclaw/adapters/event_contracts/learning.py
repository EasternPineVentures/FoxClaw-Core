"""Forecast Desk learning receipts.

Learning receipts close the loop from forecast -> paper outcome -> calibration signal
without mutating future probabilities or granting execution authority.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from .calibration import brier_score
from .contracts import ForecastReceipt
from .markets import dumps_json
from .paper import PaperOutcome

_ZERO = Decimal("0")
_ONE = Decimal("1")


@dataclass(frozen=True)
class ForecastLearningReceipt:
    learning_receipt_id: str
    market_id: str
    position_id: str
    forecast_receipt_hash: str
    dossier_hash: str
    side: str
    resolved_outcome: str
    outcome_yes: bool | None
    forecast_probability: Decimal
    market_yes_probability: Decimal | None
    forecast_brier: Decimal | None
    market_brier: Decimal | None
    brier_edge: Decimal | None
    usable_edge: Decimal
    paper_net_result: Decimal
    paper_result_label: str
    decision_quality: str
    learning_signal: str
    evidence_quality: Decimal
    engine_tier: str
    mode: str
    public_information_only: bool
    founder_private_reasoning_excluded: bool
    public_safe_export_candidate: bool
    created_at: datetime
    can_set_probability: bool = False
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False

    def __post_init__(self) -> None:
        if not self.learning_receipt_id.startswith("sha256:"):
            raise ValueError("learning_receipt_id must be sha256-prefixed")
        if not self.forecast_receipt_hash.startswith("sha256:"):
            raise ValueError("forecast_receipt_hash must be sha256-prefixed")
        if not self.dossier_hash.startswith("sha256:"):
            raise ValueError("dossier_hash must be sha256-prefixed")
        if self.side not in {"yes", "no", "none"}:
            raise ValueError("side must be yes, no, or none")
        if self.resolved_outcome not in {"yes", "no", "void"}:
            raise ValueError("resolved_outcome must be yes, no, or void")
        if self.outcome_yes is None and self.resolved_outcome != "void":
            raise ValueError("non-void outcomes must carry outcome_yes")
        for label in (
            "forecast_probability",
            "usable_edge",
            "paper_net_result",
            "evidence_quality",
        ):
            _finite_decimal(getattr(self, label), label)
        for label in ("market_yes_probability", "forecast_brier", "market_brier", "brier_edge"):
            value = getattr(self, label)
            if value is not None:
                _finite_decimal(value, label)
        if self.paper_result_label not in {"paper_profit", "paper_loss", "paper_flat"}:
            raise ValueError("unsupported paper_result_label")
        if self.decision_quality not in {
            "foxclaw_outperformed_market",
            "market_outperformed_foxclaw",
            "matched_market",
            "no_market_baseline",
            "void_resolution",
        }:
            raise ValueError("unsupported decision_quality")
        if self.learning_signal not in {"reinforce", "review", "neutral", "void"}:
            raise ValueError("unsupported learning_signal")
        if self.mode != "PAPER":
            raise ValueError("learning receipts are PAPER mode in this authority phase")
        if not self.public_information_only:
            raise ValueError("learning receipts require public information only")
        if not self.founder_private_reasoning_excluded:
            raise ValueError("learning receipts must exclude founder-private reasoning")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        if (
            self.can_set_probability
            or self.can_submit_order
            or self.can_move_funds
            or self.live_execution_allowed
        ):
            raise ValueError("learning receipts cannot grant authority")


def build_learning_receipt(
    *,
    forecast: ForecastReceipt,
    outcome: PaperOutcome,
    created_at: datetime | None = None,
) -> ForecastLearningReceipt:
    if forecast.market_id != outcome.market_id:
        raise ValueError("forecast and outcome market_id must match")
    outcome_yes = _outcome_yes(outcome.resolved_outcome)
    market_yes = _market_yes_probability(forecast)
    forecast_brier_value = _single_brier(forecast.independent_probability, outcome_yes)
    market_brier_value = _single_brier(market_yes, outcome_yes) if market_yes is not None else None
    brier_edge = (
        market_brier_value - forecast_brier_value
        if market_brier_value is not None and forecast_brier_value is not None
        else None
    )
    paper_label = _paper_result_label(outcome.net_result)
    decision_quality = _decision_quality(brier_edge=brier_edge, outcome_yes=outcome_yes)
    learning_signal = _learning_signal(
        brier_edge=brier_edge,
        net_result=outcome.net_result,
        outcome_yes=outcome_yes,
    )
    payload = {
        "market_id": forecast.market_id,
        "position_id": outcome.position_id,
        "forecast_receipt_hash": receipt_hash(forecast),
        "dossier_hash": forecast.dossier_hash,
        "side": forecast.side,
        "resolved_outcome": outcome.resolved_outcome,
        "outcome_yes": outcome_yes,
        "forecast_probability": forecast.independent_probability,
        "market_yes_probability": market_yes,
        "forecast_brier": forecast_brier_value,
        "market_brier": market_brier_value,
        "brier_edge": brier_edge,
        "usable_edge": forecast.usable_edge,
        "paper_net_result": outcome.net_result,
        "paper_result_label": paper_label,
        "decision_quality": decision_quality,
        "learning_signal": learning_signal,
        "evidence_quality": forecast.evidence_quality,
        "engine_tier": forecast.engine_tier,
        "mode": "PAPER",
        "public_information_only": True,
        "founder_private_reasoning_excluded": True,
        "public_safe_export_candidate": outcome.resolved_outcome != "void",
        "created_at": (created_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0),
    }
    return ForecastLearningReceipt(
        learning_receipt_id=learning_receipt_id(payload),
        **payload,
    )


def receipt_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(dumps_json(value).encode("utf-8")).hexdigest()


def learning_receipt_id(payload: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(dumps_json(payload).encode("utf-8")).hexdigest()


def _market_yes_probability(forecast: ForecastReceipt) -> Decimal | None:
    if forecast.market_probability is None:
        return None
    if forecast.side == "yes":
        return forecast.market_probability
    if forecast.side == "no":
        return _ONE - forecast.market_probability
    return forecast.market_probability


def _single_brier(probability: Decimal | None, outcome_yes: bool | None) -> Decimal | None:
    if probability is None or outcome_yes is None:
        return None
    return brier_score([probability], [outcome_yes])


def _outcome_yes(resolved_outcome: str) -> bool | None:
    if resolved_outcome == "yes":
        return True
    if resolved_outcome == "no":
        return False
    if resolved_outcome == "void":
        return None
    raise ValueError("resolved_outcome must be yes, no, or void")


def _paper_result_label(net_result: Decimal) -> str:
    if net_result > _ZERO:
        return "paper_profit"
    if net_result < _ZERO:
        return "paper_loss"
    return "paper_flat"


def _decision_quality(*, brier_edge: Decimal | None, outcome_yes: bool | None) -> str:
    if outcome_yes is None:
        return "void_resolution"
    if brier_edge is None:
        return "no_market_baseline"
    if brier_edge > _ZERO:
        return "foxclaw_outperformed_market"
    if brier_edge < _ZERO:
        return "market_outperformed_foxclaw"
    return "matched_market"


def _learning_signal(
    *,
    brier_edge: Decimal | None,
    net_result: Decimal,
    outcome_yes: bool | None,
) -> str:
    if outcome_yes is None:
        return "void"
    if brier_edge is not None and brier_edge > _ZERO and net_result >= _ZERO:
        return "reinforce"
    if (brier_edge is not None and brier_edge < _ZERO) or net_result < _ZERO:
        return "review"
    return "neutral"


def _finite_decimal(value: Any, label: str) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise TypeError(f"{label} must be finite Decimal")
