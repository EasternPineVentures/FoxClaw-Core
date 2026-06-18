from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from foxclaw.adapters.event_contracts.kalshi.historical import (
    market_belongs_to_historical,
    merge_market_pages,
    parse_historical_cutoff,
)
from foxclaw.adapters.event_contracts.kalshi.normalize import (
    normalize_event,
    normalize_market,
    normalize_series,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "kalshi"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_series_normalization_preserves_settlement_source_and_rules():
    series = normalize_series(_load("series_page.json")["series"][0])
    assert series.series_id == "KXJOBLESS"
    assert series.category == "economics"
    assert series.rules_url == "https://kalshi.example/rules/KXJOBLESS"
    assert series.settlement_sources == ("Department of Labor | https://www.dol.gov/",)


def test_event_normalization_accepts_current_settlement_sources_field():
    event = normalize_event(_load("events_page.json")["events"][0])
    assert event.event_id == "KXJOBLESS-26JUN18"
    assert event.status == "open"
    assert event.strike_date is not None
    assert event.settlement_sources[0].startswith("Department of Labor")


def test_market_normalization_uses_decimal_fixed_point_values():
    market = normalize_market(_load("markets_page.json")["markets"][0])
    assert market.market_id == "KXJOBLESS-26JUN18-T250"
    assert market.yes_bid == Decimal("0.4200")
    assert market.no_bid == Decimal("0.5700")
    assert market.volume == Decimal("118.00")
    assert market.resolution_rule_text is not None


def test_market_normalization_rejects_float_money():
    with pytest.raises(TypeError):
        normalize_market(_load("malformed_market.json")["market"])


def test_historical_cutoff_routes_old_settled_markets():
    cutoff = parse_historical_cutoff(_load("historical_cutoff.json"))
    old_market = _load("historical_market.json")["market"]
    assert market_belongs_to_historical(old_market, cutoff) is True


def test_historical_live_merge_dedupes_deterministically():
    live = [{"ticker": "B"}, {"ticker": "A"}]
    historical = [{"ticker": "A", "source": "historical"}, {"ticker": "C"}]
    merged = merge_market_pages(live, historical)
    assert [m["ticker"] for m in merged] == ["A", "B", "C"]
    assert merged[0] == {"ticker": "A"}
