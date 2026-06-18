"""Historical/live routing helpers for Kalshi market data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping

from .models import parse_datetime_utc, require_mapping


@dataclass(frozen=True)
class HistoricalCutoff:
    market_settled_ts: datetime
    trades_created_ts: datetime
    orders_updated_ts: datetime


def parse_historical_cutoff(raw: Mapping[str, Any]) -> HistoricalCutoff:
    payload = require_mapping(raw, label="historical cutoff")
    market = parse_datetime_utc(payload.get("market_settled_ts"), label="market_settled_ts")
    trades = parse_datetime_utc(payload.get("trades_created_ts"), label="trades_created_ts")
    orders = parse_datetime_utc(payload.get("orders_updated_ts"), label="orders_updated_ts")
    if market is None or trades is None or orders is None:
        raise ValueError("historical cutoff missing required timestamp")
    return HistoricalCutoff(market_settled_ts=market, trades_created_ts=trades, orders_updated_ts=orders)


def market_belongs_to_historical(market: Mapping[str, Any], cutoff: HistoricalCutoff) -> bool:
    settled_at = parse_datetime_utc(
        market.get("settled_time") or market.get("settlement_time") or market.get("close_time"),
        label="market settlement time",
    )
    return bool(settled_at and settled_at < cutoff.market_settled_ts)


def trade_belongs_to_historical(trade: Mapping[str, Any], cutoff: HistoricalCutoff) -> bool:
    created = parse_datetime_utc(trade.get("created_time"), label="created_time")
    return bool(created and created < cutoff.trades_created_ts)


def merge_market_pages(*pages: Iterable[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    """Merge live and historical market pages deterministically, de-duping by ticker."""

    by_ticker: dict[str, Mapping[str, Any]] = {}
    for page in pages:
        for market in page:
            ticker = str(market.get("ticker") or market.get("market_ticker") or "").strip()
            if not ticker:
                continue
            by_ticker.setdefault(ticker, market)
    return tuple(by_ticker[key] for key in sorted(by_ticker))
