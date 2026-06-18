from __future__ import annotations

from decimal import Decimal

import pytest

from foxclaw.adapters.event_contracts.costs import cost_receipt
from foxclaw.adapters.event_contracts.kalshi.fees import KalshiFeeSchedule, estimate_fee


def test_cost_receipt_sums_versioned_costs():
    receipt = cost_receipt(
        spread_cost=Decimal("0.0100"),
        venue_fee_cost=Decimal("0.0200"),
        modeled_slippage=Decimal("0.0050"),
        capital_lock_cost=Decimal("0.0000"),
    )
    assert receipt.version == "forecast_cost_model_v1"
    assert receipt.total == Decimal("0.0350")


def test_negative_cost_or_fee_rejected():
    with pytest.raises(ValueError):
        cost_receipt(spread_cost=Decimal("-0.01"))
    with pytest.raises(ValueError):
        estimate_fee(Decimal("0.43"), Decimal("1"), schedule=KalshiFeeSchedule(taker_fee_rate=Decimal("-0.01")))
