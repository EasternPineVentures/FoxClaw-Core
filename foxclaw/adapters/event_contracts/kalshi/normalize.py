"""Normalize raw Kalshi payloads into Forecast Desk contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Mapping

from foxclaw.adapters.event_contracts.markets import (
    NormalizedEvent,
    NormalizedMarket,
    NormalizedSeries,
)

from .models import (
    optional_fixed_decimal,
    parse_datetime_utc,
    payload_hash,
    require_mapping,
    settlement_source_strings,
)

_ZERO = Decimal("0")
_ONE = Decimal("1")


def normalize_series(raw: Mapping[str, Any], *, observed_at: datetime | None = None) -> NormalizedSeries:
    payload = require_mapping(raw, label="series")
    return NormalizedSeries(
        venue="kalshi",
        series_id=_first_text(payload, "ticker", "series_ticker"),
        title=_first_text(payload, "title"),
        category=_optional_text(payload.get("category")),
        frequency=_optional_text(payload.get("frequency")),
        settlement_sources=settlement_source_strings(payload.get("settlement_sources")),
        rules_url=_optional_text(payload.get("contract_terms_url") or payload.get("contract_url")),
        observed_at=(observed_at or datetime.now(UTC)).astimezone(UTC),
        raw_payload_hash=payload_hash(payload),
    )


def normalize_event(raw: Mapping[str, Any], *, observed_at: datetime | None = None) -> NormalizedEvent:
    payload = require_mapping(raw, label="event")
    status = payload.get("status")
    if status is None:
        markets = payload.get("markets")
        if isinstance(markets, list) and markets:
            first_market = markets[0] if isinstance(markets[0], Mapping) else {}
            status = first_market.get("status")
    return NormalizedEvent(
        venue="kalshi",
        event_id=_first_text(payload, "event_ticker", "ticker"),
        series_id=_optional_text(payload.get("series_ticker")),
        title=_first_text(payload, "title", "sub_title"),
        category=_optional_text(payload.get("category")),
        status=_optional_text(status) or "unknown",
        strike_date=parse_datetime_utc(payload.get("strike_date"), label="strike_date"),
        settlement_sources=settlement_source_strings(payload.get("settlement_sources")),
        observed_at=(observed_at or datetime.now(UTC)).astimezone(UTC),
        raw_payload_hash=payload_hash(payload),
    )


def normalize_market(raw: Mapping[str, Any], *, observed_at: datetime | None = None) -> NormalizedMarket:
    payload = require_mapping(raw, label="market")
    market_id = _first_text(payload, "ticker", "market_ticker")
    title = _optional_text(payload.get("title") or payload.get("yes_title") or payload.get("yes_sub_title"))
    if not title:
        title = market_id
    close_time = parse_datetime_utc(payload.get("close_time"), label="close_time")
    expiration_time = parse_datetime_utc(
        payload.get("latest_expiration_time") or payload.get("expiration_time"),
        label="expiration_time",
    )
    return NormalizedMarket(
        venue="kalshi",
        market_id=market_id,
        event_id=_optional_text(payload.get("event_ticker")),
        series_id=_optional_text(payload.get("series_ticker")),
        title=title,
        subtitle=_optional_text(payload.get("subtitle") or payload.get("no_sub_title")),
        status=_optional_text(payload.get("status")) or "unknown",
        yes_bid=_price(payload, "yes_bid_dollars", "yes_bid"),
        yes_ask=_price(payload, "yes_ask_dollars", "yes_ask"),
        no_bid=_price(payload, "no_bid_dollars", "no_bid"),
        no_ask=_price(payload, "no_ask_dollars", "no_ask"),
        last_price=_price(payload, "last_price_dollars", "last_price", "price_dollars"),
        volume=_quantity(payload, "volume_fp", "volume"),
        open_interest=_quantity(payload, "open_interest_fp", "open_interest"),
        close_time=close_time,
        expiration_time=expiration_time,
        result=_optional_text(payload.get("result") or payload.get("settlement_value")),
        resolution_rule_text=_optional_text(
            payload.get("rules_primary")
            or payload.get("resolution_rule")
            or payload.get("market_rules")
            or payload.get("settlement_rule")
        ),
        settlement_sources=settlement_source_strings(payload.get("settlement_sources")),
        price_level_structure=_optional_text(payload.get("price_level_structure")) or "binary",
        observed_at=(observed_at or datetime.now(UTC)).astimezone(UTC),
        raw_payload_hash=payload_hash(payload),
    )


def _price(payload: Mapping[str, Any], *keys: str) -> Decimal | None:
    for key in keys:
        if key in payload:
            return optional_fixed_decimal(payload.get(key), label=key, minimum=_ZERO, maximum=_ONE)
    return None


def _quantity(payload: Mapping[str, Any], *keys: str) -> Decimal:
    for key in keys:
        if key in payload and payload.get(key) not in (None, ""):
            return optional_fixed_decimal(payload.get(key), label=key, minimum=_ZERO) or _ZERO
    return _ZERO


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_text(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        text = _optional_text(payload.get(key))
        if text:
            return text
    raise ValueError(f"missing required text field; tried {keys}")
