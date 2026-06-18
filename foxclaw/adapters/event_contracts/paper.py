"""Paper-only event-contract fills and settlements."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping

from foxclaw.adapters.event_contracts.contracts import ForecastReceipt, ResolutionReceipt
from foxclaw.adapters.event_contracts.markets import NormalizedOrderBook, to_jsonable

from .kalshi.fees import KalshiFeeSchedule, estimate_fee

_ZERO = Decimal("0")
_ONE = Decimal("1")
_Q = Decimal("0.0001")


@dataclass(frozen=True)
class PaperPosition:
    position_id: str
    market_id: str
    side: str
    requested_contracts: Decimal
    filled_contracts: Decimal
    fill_status: str
    entry_price: Decimal | None
    entry_cost: Decimal
    fee_paid: Decimal
    fee_model_version: str
    opened_at: datetime
    source_receipt_hash: str
    mode: str = "PAPER"
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class PaperOutcome:
    position_id: str
    market_id: str
    side: str
    resolved_outcome: str
    payout: Decimal
    entry_cost: Decimal
    fees: Decimal
    net_result: Decimal
    settled_at: datetime
    mode: str = "PAPER"
    can_submit_order: bool = False
    can_move_funds: bool = False


def simulate_paper_entry(
    *,
    forecast: ForecastReceipt,
    orderbook: NormalizedOrderBook,
    requested_contracts: Decimal,
    fee_schedule: KalshiFeeSchedule | None = None,
) -> PaperPosition:
    if forecast.verdict != "paper":
        raise ValueError("paper entry requires a paper forecast receipt")
    if requested_contracts <= _ZERO:
        raise ValueError("requested_contracts must be positive")
    price, available_depth = _executable_top(orderbook, forecast.side)
    if price is None or available_depth <= _ZERO:
        filled = _ZERO
        status = "none"
    else:
        filled = min(requested_contracts, available_depth)
        status = "full" if filled == requested_contracts else "partial"
    fee_schedule = fee_schedule or KalshiFeeSchedule()
    fee = estimate_fee(price or _ZERO, filled, schedule=fee_schedule)
    entry_cost = ((price or _ZERO) * filled).quantize(_Q, rounding=ROUND_HALF_UP)
    return PaperPosition(
        position_id=f"paper:{forecast.market_id}:{forecast.side}:{forecast.dossier_hash[-12:]}",
        market_id=forecast.market_id,
        side=forecast.side,
        requested_contracts=_q(requested_contracts),
        filled_contracts=_q(filled),
        fill_status=status,
        entry_price=price,
        entry_cost=entry_cost,
        fee_paid=fee,
        fee_model_version=fee_schedule.version,
        opened_at=forecast.created_at.astimezone(UTC),
        source_receipt_hash=forecast.dossier_hash,
    )


def settle_paper_position(position: PaperPosition, resolution: ResolutionReceipt) -> PaperOutcome:
    if position.market_id != resolution.market_id:
        raise ValueError("resolution market does not match position")
    if resolution.resolved_at < position.opened_at:
        raise ValueError("resolution predates paper position; replay would look ahead")
    if resolution.resolved_outcome == "void":
        payout = position.entry_cost
    elif resolution.resolved_outcome == position.side:
        payout = (position.filled_contracts * _ONE).quantize(_Q, rounding=ROUND_HALF_UP)
    else:
        payout = _ZERO
    net = (payout - position.entry_cost - position.fee_paid).quantize(_Q, rounding=ROUND_HALF_UP)
    return PaperOutcome(
        position_id=position.position_id,
        market_id=position.market_id,
        side=position.side,
        resolved_outcome=resolution.resolved_outcome,
        payout=payout,
        entry_cost=position.entry_cost,
        fees=position.fee_paid,
        net_result=net,
        settled_at=resolution.resolved_at.astimezone(UTC),
    )


def replay_positions(positions: list[PaperPosition], resolutions: Mapping[str, ResolutionReceipt]) -> dict[str, Any]:
    outcomes: list[PaperOutcome] = []
    for position in sorted(positions, key=lambda item: item.opened_at):
        resolution = resolutions.get(position.market_id)
        if resolution is None:
            continue
        outcomes.append(settle_paper_position(position, resolution))
    return {
        "mode": "PAPER",
        "positions": [to_jsonable(item) for item in positions],
        "outcomes": [to_jsonable(item) for item in outcomes],
        "net_result": format(sum((item.net_result for item in outcomes), _ZERO), "f"),
    }


def open_paper_position(market: Mapping[str, Any], side: str, stake: float) -> dict[str, Any]:
    """Compatibility wrapper for older callers; use simulate_paper_entry for real receipts."""

    return {
        "market_id": str(market.get("market_id") or market.get("ticker") or ""),
        "side": side,
        "stake": Decimal(str(stake)),
        "mode": "PAPER",
        "can_submit_order": False,
        "can_move_funds": False,
    }


def close_paper_position(position: Mapping[str, Any], resolution: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "position_id": position.get("position_id"),
        "market_id": position.get("market_id"),
        "resolved_outcome": resolution.get("resolved_outcome") or resolution.get("outcome"),
        "mode": "PAPER",
        "can_submit_order": False,
        "can_move_funds": False,
    }


def _executable_top(book: NormalizedOrderBook, side: str) -> tuple[Decimal | None, Decimal]:
    if side == "yes":
        return book.best_yes_ask, book.depth_no_at_best
    if side == "no":
        return book.best_no_ask, book.depth_yes_at_best
    raise ValueError("side must be yes or no")


def _q(value: Decimal) -> Decimal:
    return value.quantize(_Q, rounding=ROUND_HALF_UP)
