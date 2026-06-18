"""Redshift paper-execution boundary receipts.

FoxClaw owns the decision. Redshift may rehearse paper execution and return paper receipts.
This module proves that handshake without granting Redshift probability, policy, or live
execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from foxclaw.adapters.event_contracts.contracts import ForecastReceipt
from foxclaw.adapters.event_contracts.kalshi.models import payload_hash
from foxclaw.adapters.event_contracts.markets import to_jsonable

_ZERO = Decimal("0")
_ONE = Decimal("1")
_Q = Decimal("0.0001")


@dataclass(frozen=True)
class FoxClawDecisionExport:
    export_id: str
    forecast_receipt_hash: str
    market_id: str
    side: str
    verdict: str
    independent_probability: Decimal
    market_probability: Decimal | None
    usable_edge: Decimal
    costs_total: Decimal
    dossier_hash: str
    code_version: str
    created_at: datetime
    mode: str = "PAPER"
    authority_level: str = "foxclaw_decision_context_only"
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False
    can_mutate_decision: bool = False

    def __post_init__(self) -> None:
        if not self.export_id.startswith("sha256:"):
            raise ValueError("export_id must be sha256-prefixed")
        if not self.forecast_receipt_hash.startswith("sha256:"):
            raise ValueError("forecast_receipt_hash must be sha256-prefixed")
        if self.side not in {"yes", "no"}:
            raise ValueError("Redshift paper boundary requires yes/no decision side")
        if self.verdict != "paper":
            raise ValueError("Redshift paper boundary only accepts paper forecast decisions")
        _require_decimal(self.independent_probability, "independent_probability", minimum=_ZERO, maximum=_ONE)
        if self.market_probability is not None:
            _require_decimal(self.market_probability, "market_probability", minimum=_ZERO, maximum=_ONE)
        _require_decimal(self.usable_edge, "usable_edge")
        _require_decimal(self.costs_total, "costs_total", minimum=_ZERO)
        if not self.dossier_hash.startswith("sha256:"):
            raise ValueError("dossier_hash must be sha256-prefixed")
        _require_aware(self.created_at, "created_at")
        if self.mode != "PAPER":
            raise ValueError("FoxClaw decision exports are PAPER mode")
        if self.authority_level != "foxclaw_decision_context_only":
            raise ValueError("FoxClaw decision exports are context-only")
        if any(
            (
                self.can_submit_order,
                self.can_move_funds,
                self.live_execution_allowed,
                self.can_mutate_decision,
            )
        ):
            raise ValueError("FoxClaw decision exports cannot grant authority")


@dataclass(frozen=True)
class RedshiftPaperExecutionReceipt:
    execution_receipt_id: str
    source_forecast_receipt_hash: str
    decision_export_id: str
    decision_snapshot_hash: str
    market_id: str
    side: str
    fill_status: str
    requested_contracts: Decimal
    filled_contracts: Decimal
    fill_price: Decimal
    slippage: Decimal
    fees: Decimal
    executed_at: datetime
    lab_id: str
    mode: str = "PAPER"
    authority_level: str = "redshift_paper_rehearsal"
    redshift_capital_effect: str = "none"
    live_order_id: str | None = None
    account_id: str | None = None
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False
    can_mutate_foxclaw_decision: bool = False

    def __post_init__(self) -> None:
        if not self.execution_receipt_id.startswith("sha256:"):
            raise ValueError("execution_receipt_id must be sha256-prefixed")
        for label in ("source_forecast_receipt_hash", "decision_export_id", "decision_snapshot_hash"):
            if not str(getattr(self, label)).startswith("sha256:"):
                raise ValueError(f"{label} must be sha256-prefixed")
        if self.side not in {"yes", "no"}:
            raise ValueError("side must be yes or no")
        if self.fill_status not in {"none", "partial", "full"}:
            raise ValueError("unsupported fill_status")
        _require_decimal(self.requested_contracts, "requested_contracts", minimum=_ZERO)
        _require_decimal(self.filled_contracts, "filled_contracts", minimum=_ZERO)
        _require_decimal(self.fill_price, "fill_price", minimum=_ZERO, maximum=_ONE)
        _require_decimal(self.slippage, "slippage", minimum=_ZERO)
        _require_decimal(self.fees, "fees", minimum=_ZERO)
        if self.filled_contracts > self.requested_contracts:
            raise ValueError("filled_contracts cannot exceed requested_contracts")
        if self.fill_status == "none" and self.filled_contracts != _ZERO:
            raise ValueError("none fill_status requires zero filled_contracts")
        if self.fill_status == "full" and self.filled_contracts != self.requested_contracts:
            raise ValueError("full fill_status requires complete fill")
        _require_aware(self.executed_at, "executed_at")
        if not str(self.lab_id).strip():
            raise ValueError("lab_id is required")
        if self.mode != "PAPER":
            raise ValueError("Redshift execution receipts are PAPER mode")
        if self.authority_level != "redshift_paper_rehearsal":
            raise ValueError("Redshift paper execution is rehearsal only")
        if self.redshift_capital_effect != "none":
            raise ValueError("Redshift paper receipts cannot have capital effect")
        if self.live_order_id is not None or self.account_id is not None:
            raise ValueError("Redshift paper receipts cannot carry live order or account IDs")
        if any(
            (
                self.can_submit_order,
                self.can_move_funds,
                self.live_execution_allowed,
                self.can_mutate_foxclaw_decision,
            )
        ):
            raise ValueError("Redshift paper receipts cannot grant authority")


@dataclass(frozen=True)
class RedshiftPaperOutcomeReceipt:
    outcome_receipt_id: str
    execution_receipt_id: str
    decision_export_id: str
    market_id: str
    side: str
    resolved_outcome: str
    payout: Decimal
    entry_cost: Decimal
    fees: Decimal
    net_result: Decimal
    settled_at: datetime
    mode: str = "PAPER"
    authority_level: str = "redshift_paper_rehearsal"
    redshift_capital_effect: str = "none"
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False

    def __post_init__(self) -> None:
        for label in ("outcome_receipt_id", "execution_receipt_id", "decision_export_id"):
            if not str(getattr(self, label)).startswith("sha256:"):
                raise ValueError(f"{label} must be sha256-prefixed")
        if self.side not in {"yes", "no"}:
            raise ValueError("side must be yes or no")
        if self.resolved_outcome not in {"yes", "no", "void"}:
            raise ValueError("resolved_outcome must be yes, no, or void")
        for label in ("payout", "entry_cost", "fees", "net_result"):
            _require_decimal(getattr(self, label), label)
        _require_aware(self.settled_at, "settled_at")
        if self.mode != "PAPER":
            raise ValueError("Redshift outcome receipts are PAPER mode")
        if self.authority_level != "redshift_paper_rehearsal":
            raise ValueError("Redshift paper outcomes are rehearsal only")
        if self.redshift_capital_effect != "none":
            raise ValueError("Redshift paper outcomes cannot have capital effect")
        if self.can_submit_order or self.can_move_funds or self.live_execution_allowed:
            raise ValueError("Redshift paper outcomes cannot grant authority")


def export_foxclaw_decision(forecast: ForecastReceipt) -> FoxClawDecisionExport:
    """Create the context-only decision packet Redshift may consume."""

    if forecast.can_submit_order or forecast.can_move_funds or forecast.live_execution_allowed:
        raise ValueError("cannot export a forecast receipt with live authority")
    source_hash = payload_hash(to_jsonable(forecast))
    export_payload = {
        "kind": "foxclaw_decision_export",
        "forecast_receipt_hash": source_hash,
        "market_id": forecast.market_id,
        "side": forecast.side,
        "dossier_hash": forecast.dossier_hash,
    }
    return FoxClawDecisionExport(
        export_id=payload_hash(export_payload),
        forecast_receipt_hash=source_hash,
        market_id=forecast.market_id,
        side=forecast.side,
        verdict=forecast.verdict,
        independent_probability=forecast.independent_probability,
        market_probability=forecast.market_probability,
        usable_edge=forecast.usable_edge,
        costs_total=forecast.costs_total,
        dossier_hash=forecast.dossier_hash,
        code_version=forecast.code_version,
        created_at=forecast.created_at.astimezone(UTC),
    )


def rehearse_redshift_paper_execution(
    decision: FoxClawDecisionExport,
    *,
    requested_contracts: Decimal,
    fill_price: Decimal,
    filled_contracts: Decimal | None = None,
    fees: Decimal = _ZERO,
    slippage: Decimal = _ZERO,
    executed_at: datetime | None = None,
    lab_id: str = "redshift_paper_boundary_v1",
) -> RedshiftPaperExecutionReceipt:
    """Return Redshift's paper execution receipt without mutating the FoxClaw decision."""

    _require_decimal(requested_contracts, "requested_contracts", minimum=_ZERO)
    _require_decimal(fill_price, "fill_price", minimum=_ZERO, maximum=_ONE)
    filled = requested_contracts if filled_contracts is None else filled_contracts
    _require_decimal(filled, "filled_contracts", minimum=_ZERO)
    status = _fill_status(requested_contracts, filled)
    executed = (executed_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    decision_hash = decision_snapshot_hash(decision)
    payload = {
        "kind": "redshift_paper_execution",
        "decision_export_id": decision.export_id,
        "decision_snapshot_hash": decision_hash,
        "requested_contracts": _fmt(requested_contracts),
        "filled_contracts": _fmt(filled),
        "fill_price": _fmt(fill_price),
        "fees": _fmt(fees),
        "slippage": _fmt(slippage),
        "executed_at": executed.isoformat(),
        "lab_id": lab_id,
    }
    return RedshiftPaperExecutionReceipt(
        execution_receipt_id=payload_hash(payload),
        source_forecast_receipt_hash=decision.forecast_receipt_hash,
        decision_export_id=decision.export_id,
        decision_snapshot_hash=decision_hash,
        market_id=decision.market_id,
        side=decision.side,
        fill_status=status,
        requested_contracts=_q(requested_contracts),
        filled_contracts=_q(filled),
        fill_price=_q(fill_price),
        slippage=_q(slippage),
        fees=_q(fees),
        executed_at=executed,
        lab_id=lab_id,
    )


def settle_redshift_paper_execution(
    execution: RedshiftPaperExecutionReceipt,
    *,
    resolved_outcome: str,
    settled_at: datetime | None = None,
) -> RedshiftPaperOutcomeReceipt:
    settled = (settled_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    entry_cost = _q(execution.fill_price * execution.filled_contracts)
    if resolved_outcome == "void":
        payout = entry_cost
    elif resolved_outcome == execution.side:
        payout = _q(execution.filled_contracts)
    elif resolved_outcome in {"yes", "no"}:
        payout = _ZERO
    else:
        raise ValueError("resolved_outcome must be yes, no, or void")
    net = _q(payout - entry_cost - execution.fees)
    payload = {
        "kind": "redshift_paper_outcome",
        "execution_receipt_id": execution.execution_receipt_id,
        "resolved_outcome": resolved_outcome,
        "payout": _fmt(payout),
        "entry_cost": _fmt(entry_cost),
        "fees": _fmt(execution.fees),
        "net_result": _fmt(net),
        "settled_at": settled.isoformat(),
    }
    return RedshiftPaperOutcomeReceipt(
        outcome_receipt_id=payload_hash(payload),
        execution_receipt_id=execution.execution_receipt_id,
        decision_export_id=execution.decision_export_id,
        market_id=execution.market_id,
        side=execution.side,
        resolved_outcome=resolved_outcome,
        payout=payout,
        entry_cost=entry_cost,
        fees=execution.fees,
        net_result=net,
        settled_at=settled,
    )


def verify_execution_links_decision(
    decision: FoxClawDecisionExport,
    execution: RedshiftPaperExecutionReceipt,
) -> bool:
    return (
        execution.decision_export_id == decision.export_id
        and execution.source_forecast_receipt_hash == decision.forecast_receipt_hash
        and execution.decision_snapshot_hash == decision_snapshot_hash(decision)
        and execution.market_id == decision.market_id
        and execution.side == decision.side
    )


def decision_snapshot_hash(decision: FoxClawDecisionExport) -> str:
    return payload_hash(
        {
            "export_id": decision.export_id,
            "forecast_receipt_hash": decision.forecast_receipt_hash,
            "market_id": decision.market_id,
            "side": decision.side,
            "verdict": decision.verdict,
            "independent_probability": _fmt(decision.independent_probability),
            "market_probability": _fmt(decision.market_probability),
            "usable_edge": _fmt(decision.usable_edge),
            "costs_total": _fmt(decision.costs_total),
            "dossier_hash": decision.dossier_hash,
            "code_version": decision.code_version,
            "mode": decision.mode,
            "authority_level": decision.authority_level,
        }
    )


def _fill_status(requested: Decimal, filled: Decimal) -> str:
    if filled == _ZERO:
        return "none"
    if filled == requested:
        return "full"
    if _ZERO < filled < requested:
        return "partial"
    raise ValueError("filled_contracts cannot exceed requested_contracts")


def _require_decimal(
    value: Any,
    label: str,
    *,
    minimum: Decimal | None = None,
    maximum: Decimal | None = None,
) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal):
        raise TypeError(f"{label} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must be <= {maximum}")
    return value


def _require_aware(value: datetime, label: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")


def _q(value: Decimal) -> Decimal:
    return value.quantize(_Q, rounding=ROUND_HALF_UP)


def _fmt(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")
