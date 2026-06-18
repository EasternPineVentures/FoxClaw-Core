"""Kalshi bid-only order-book normalization."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterable, Mapping

from foxclaw.adapters.event_contracts.markets import NormalizedOrderBook, PriceLevel

from .models import fixed_decimal, payload_hash, require_mapping, require_sequence

_ZERO = Decimal("0")
_ONE = Decimal("1")


def normalize_orderbook(
    raw: Mapping[str, Any],
    *,
    market_id: str,
    venue: str = "kalshi",
    observed_at: datetime | None = None,
) -> NormalizedOrderBook:
    payload = require_mapping(raw, label="orderbook payload")
    body = payload.get("orderbook_fp") or payload.get("orderbook")
    book = require_mapping(body, label="orderbook_fp")
    yes_raw = book.get("yes_dollars", book.get("yes", ()))
    no_raw = book.get("no_dollars", book.get("no", ()))
    yes_bids = _levels(yes_raw, label="yes_dollars")
    no_bids = _levels(no_raw, label="no_dollars")

    best_yes_bid, depth_yes = _best(yes_bids)
    best_no_bid, depth_no = _best(no_bids)
    best_yes_ask = (_ONE - best_no_bid) if best_no_bid is not None else None
    best_no_ask = (_ONE - best_yes_bid) if best_yes_bid is not None else None
    yes_spread = (best_yes_ask - best_yes_bid) if best_yes_bid is not None and best_yes_ask is not None else None
    no_spread = (best_no_ask - best_no_bid) if best_no_bid is not None and best_no_ask is not None else None

    invalid_reasons: list[str] = []
    if yes_spread is not None and yes_spread < _ZERO:
        invalid_reasons.append("crossed_yes_book")
    if no_spread is not None and no_spread < _ZERO:
        invalid_reasons.append("crossed_no_book")
    if not yes_bids and not no_bids:
        invalid_reasons.append("empty_book")

    return NormalizedOrderBook(
        venue=venue,
        market_id=str(market_id),
        observed_at=(observed_at or datetime.now(UTC)).astimezone(UTC),
        yes_bids=yes_bids,
        no_bids=no_bids,
        best_yes_bid=best_yes_bid,
        best_yes_ask=best_yes_ask,
        best_no_bid=best_no_bid,
        best_no_ask=best_no_ask,
        yes_spread=yes_spread,
        no_spread=no_spread,
        depth_yes_at_best=depth_yes,
        depth_no_at_best=depth_no,
        raw_payload_hash=payload_hash(payload),
        is_tradeable=not invalid_reasons,
        invalid_reason=",".join(invalid_reasons) if invalid_reasons else None,
    )


def _levels(raw_levels: Any, *, label: str) -> tuple[PriceLevel, ...]:
    seq = require_sequence(raw_levels, label=label)
    by_price: dict[Decimal, Decimal] = {}
    for idx, raw_level in enumerate(seq):
        level = require_sequence(raw_level, label=f"{label}[{idx}]")
        if len(level) != 2:
            raise ValueError(f"{label}[{idx}] must be [price_dollars, count_fp]")
        price = fixed_decimal(level[0], label=f"{label}[{idx}].price", minimum=_ZERO, maximum=_ONE)
        quantity = fixed_decimal(level[1], label=f"{label}[{idx}].quantity", minimum=_ZERO)
        by_price[price] = by_price.get(price, _ZERO) + quantity
    return tuple(PriceLevel(price=p, quantity=q) for p, q in sorted(by_price.items(), reverse=True))


def _best(levels: Iterable[PriceLevel]) -> tuple[Decimal | None, Decimal]:
    levels_tuple = tuple(levels)
    if not levels_tuple:
        return None, _ZERO
    best_price = levels_tuple[0].price
    depth = sum((level.quantity for level in levels_tuple if level.price == best_price), _ZERO)
    return best_price, depth
