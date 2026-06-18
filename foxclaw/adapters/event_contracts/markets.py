"""Normalized event-contract market models.

Venue vocabulary stays in this adapter package. The engine never sees Kalshi tickers,
YES/NO book structure, or raw venue payloads; callers translate those into neutral
decision inputs at the adapter border.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Mapping

_ZERO = Decimal("0")
_ONE = Decimal("1")


def _require_decimal(value: Any, *, label: str, lower: Decimal | None = None,
                     upper: Decimal | None = None) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal):
        raise TypeError(f"{label} must be Decimal, got {type(value).__name__}")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite, got {value!r}")
    if lower is not None and value < lower:
        raise ValueError(f"{label} must be >= {lower}, got {value!r}")
    if upper is not None and value > upper:
        raise ValueError(f"{label} must be <= {upper}, got {value!r}")
    return value


def _require_optional_decimal(value: Any, *, label: str, lower: Decimal | None = None,
                              upper: Decimal | None = None) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal(value, label=label, lower=lower, upper=upper)


def _require_utc_datetime(value: Any, *, label: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{label} must be datetime, got {type(value).__name__}")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _require_nonempty(value: Any, *, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _tuple_of_strings(values: tuple[str, ...], *, label: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{label} must be a tuple")
    out = tuple(str(v).strip() for v in values if str(v).strip())
    return out


@dataclass(frozen=True)
class PriceLevel:
    """One bid level in fixed-point dollars and contract count."""

    price: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        _require_decimal(self.price, label="price", lower=_ZERO, upper=_ONE)
        _require_decimal(self.quantity, label="quantity", lower=_ZERO)


@dataclass(frozen=True)
class NormalizedOrderBook:
    """Executable binary book reconstructed from venue bid-only data."""

    venue: str
    market_id: str
    observed_at: datetime
    yes_bids: tuple[PriceLevel, ...]
    no_bids: tuple[PriceLevel, ...]
    best_yes_bid: Decimal | None
    best_yes_ask: Decimal | None
    best_no_bid: Decimal | None
    best_no_ask: Decimal | None
    yes_spread: Decimal | None
    no_spread: Decimal | None
    depth_yes_at_best: Decimal
    depth_no_at_best: Decimal
    raw_payload_hash: str
    is_tradeable: bool = True
    invalid_reason: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.venue, label="venue")
        _require_nonempty(self.market_id, label="market_id")
        _require_utc_datetime(self.observed_at, label="observed_at")
        if not isinstance(self.yes_bids, tuple) or not all(isinstance(x, PriceLevel) for x in self.yes_bids):
            raise TypeError("yes_bids must be a tuple of PriceLevel")
        if not isinstance(self.no_bids, tuple) or not all(isinstance(x, PriceLevel) for x in self.no_bids):
            raise TypeError("no_bids must be a tuple of PriceLevel")
        for label in ("best_yes_bid", "best_yes_ask", "best_no_bid", "best_no_ask"):
            _require_optional_decimal(getattr(self, label), label=label, lower=_ZERO, upper=_ONE)
        for label in ("yes_spread", "no_spread"):
            _require_optional_decimal(getattr(self, label), label=label)
        _require_decimal(self.depth_yes_at_best, label="depth_yes_at_best", lower=_ZERO)
        _require_decimal(self.depth_no_at_best, label="depth_no_at_best", lower=_ZERO)
        _require_nonempty(self.raw_payload_hash, label="raw_payload_hash")
        if not isinstance(self.is_tradeable, bool):
            raise TypeError("is_tradeable must be bool")
        if not self.is_tradeable and not self.invalid_reason:
            raise ValueError("invalid books must carry invalid_reason")


@dataclass(frozen=True)
class NormalizedSeries:
    venue: str
    series_id: str
    title: str
    category: str | None
    frequency: str | None
    settlement_sources: tuple[str, ...]
    rules_url: str | None
    observed_at: datetime
    raw_payload_hash: str

    def __post_init__(self) -> None:
        _require_nonempty(self.venue, label="venue")
        _require_nonempty(self.series_id, label="series_id")
        _require_nonempty(self.title, label="title")
        _tuple_of_strings(self.settlement_sources, label="settlement_sources")
        _require_utc_datetime(self.observed_at, label="observed_at")
        _require_nonempty(self.raw_payload_hash, label="raw_payload_hash")


@dataclass(frozen=True)
class NormalizedEvent:
    venue: str
    event_id: str
    series_id: str | None
    title: str
    category: str | None
    status: str
    strike_date: datetime | None
    settlement_sources: tuple[str, ...]
    observed_at: datetime
    raw_payload_hash: str

    def __post_init__(self) -> None:
        _require_nonempty(self.venue, label="venue")
        _require_nonempty(self.event_id, label="event_id")
        _require_nonempty(self.title, label="title")
        _require_nonempty(self.status, label="status")
        if self.strike_date is not None:
            _require_utc_datetime(self.strike_date, label="strike_date")
        _tuple_of_strings(self.settlement_sources, label="settlement_sources")
        _require_utc_datetime(self.observed_at, label="observed_at")
        _require_nonempty(self.raw_payload_hash, label="raw_payload_hash")


@dataclass(frozen=True)
class NormalizedMarket:
    venue: str
    market_id: str
    event_id: str | None
    series_id: str | None
    title: str
    subtitle: str | None
    status: str
    yes_bid: Decimal | None
    yes_ask: Decimal | None
    no_bid: Decimal | None
    no_ask: Decimal | None
    last_price: Decimal | None
    volume: Decimal
    open_interest: Decimal
    close_time: datetime | None
    expiration_time: datetime | None
    result: str | None
    resolution_rule_text: str | None
    settlement_sources: tuple[str, ...]
    price_level_structure: str
    observed_at: datetime
    raw_payload_hash: str

    def __post_init__(self) -> None:
        _require_nonempty(self.venue, label="venue")
        _require_nonempty(self.market_id, label="market_id")
        _require_nonempty(self.title, label="title")
        _require_nonempty(self.status, label="status")
        for label in ("yes_bid", "yes_ask", "no_bid", "no_ask", "last_price"):
            _require_optional_decimal(getattr(self, label), label=label, lower=_ZERO, upper=_ONE)
        _require_decimal(self.volume, label="volume", lower=_ZERO)
        _require_decimal(self.open_interest, label="open_interest", lower=_ZERO)
        if self.close_time is not None:
            _require_utc_datetime(self.close_time, label="close_time")
        if self.expiration_time is not None:
            _require_utc_datetime(self.expiration_time, label="expiration_time")
        _tuple_of_strings(self.settlement_sources, label="settlement_sources")
        _require_nonempty(self.price_level_structure, label="price_level_structure")
        _require_utc_datetime(self.observed_at, label="observed_at")
        _require_nonempty(self.raw_payload_hash, label="raw_payload_hash")


def to_jsonable(value: Any) -> Any:
    """Return a deterministic JSON-compatible view for receipts and CLIs."""

    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): to_jsonable(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list)):
        return [to_jsonable(v) for v in value]
    return value


def dumps_json(value: Any) -> str:
    return json.dumps(to_jsonable(value), sort_keys=True, separators=(",", ":"))


def normalize_market(raw: Mapping[str, Any]) -> NormalizedMarket:
    """Normalize one Kalshi market payload into the Forecast Desk contract."""

    from .kalshi.normalize import normalize_market as _normalize_market

    return _normalize_market(raw)
