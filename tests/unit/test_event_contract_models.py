from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from foxclaw.adapters.event_contracts.markets import (
    NormalizedMarket,
    PriceLevel,
    dumps_json,
)


def test_price_level_requires_decimal_not_float():
    with pytest.raises(TypeError):
        PriceLevel(price=0.42, quantity=Decimal("10.00"))  # type: ignore[arg-type]


def test_price_level_rejects_out_of_band_price():
    with pytest.raises(ValueError):
        PriceLevel(price=Decimal("1.01"), quantity=Decimal("10.00"))


def test_normalized_market_serializes_decimal_and_utc_stably():
    market = NormalizedMarket(
        venue="kalshi",
        market_id="KXTEST",
        event_id="KXEVENT",
        series_id="KXSERIES",
        title="Fixture market",
        subtitle=None,
        status="open",
        yes_bid=Decimal("0.4200"),
        yes_ask=Decimal("0.4300"),
        no_bid=Decimal("0.5700"),
        no_ask=Decimal("0.5800"),
        last_price=None,
        volume=Decimal("10.00"),
        open_interest=Decimal("2.00"),
        close_time=None,
        expiration_time=None,
        result=None,
        resolution_rule_text="Public rule",
        settlement_sources=("Public source | https://example.invalid",),
        price_level_structure="binary",
        observed_at=datetime(2026, 6, 18, tzinfo=UTC),
        raw_payload_hash="sha256:test",
    )
    encoded = dumps_json(market)
    assert '"yes_bid":"0.4200"' in encoded
    assert '"observed_at":"2026-06-18T00:00:00Z"' in encoded
