from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from foxclaw.adapters.event_contracts.dossiers import build_dossier
from foxclaw.adapters.event_contracts.kalshi.normalize import normalize_market
from foxclaw.adapters.event_contracts.kalshi.orderbook import normalize_orderbook
from foxclaw.adapters.event_contracts.paper import (
    replay_positions,
    settle_paper_position,
    simulate_paper_entry,
)
from foxclaw.adapters.event_contracts.resolution import record_resolution
from foxclaw.adapters.event_contracts.scoring import assess_forecast

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "kalshi"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _forecast():
    market = replace(normalize_market(_load("market_detail.json")["market"]), yes_ask=Decimal("0.4300"), no_ask=None)
    dossier = build_dossier(
        market,
        [
            {
                "source_id": "official",
                "title": "Official",
                "url": "https://example.invalid/official",
                "source_classification": "public",
                "independence_group": "official",
            }
        ],
    )
    return assess_forecast(
        market=market,
        dossier=dossier,
        independent_probability=Decimal("0.6200"),
    )


def test_paper_entry_uses_executable_ask_not_midpoint_and_respects_depth():
    book = normalize_orderbook(_load("orderbook.json"), market_id="KXJOBLESS-26JUN18-T250")
    position = simulate_paper_entry(
        forecast=_forecast(),
        orderbook=book,
        requested_contracts=Decimal("10.00"),
    )
    assert position.entry_price == Decimal("0.4300")
    assert position.filled_contracts == Decimal("7.0000")
    assert position.fill_status == "partial"
    assert position.entry_cost == Decimal("3.0100")
    assert position.mode == "PAPER"
    assert position.can_submit_order is False


def test_paper_settlement_computes_net_result_after_costs():
    book = normalize_orderbook(_load("orderbook.json"), market_id="KXJOBLESS-26JUN18-T250")
    position = simulate_paper_entry(
        forecast=_forecast(),
        orderbook=book,
        requested_contracts=Decimal("7.00"),
    )
    resolution = record_resolution(
        {"market_id": position.market_id},
        "yes",
        "https://example.invalid/result",
        resolved_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
    )
    outcome = settle_paper_position(position, resolution)
    assert outcome.payout == Decimal("7.0000")
    assert outcome.net_result == Decimal("3.9900")
    assert outcome.can_move_funds is False


def test_replay_manifest_is_paper_labeled():
    book = normalize_orderbook(_load("orderbook.json"), market_id="KXJOBLESS-26JUN18-T250")
    position = simulate_paper_entry(
        forecast=_forecast(),
        orderbook=book,
        requested_contracts=Decimal("1.00"),
    )
    resolution = record_resolution(
        {"market_id": position.market_id},
        "no",
        "https://example.invalid/result",
        resolved_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
    )
    manifest = replay_positions([position], {position.market_id: resolution})
    assert manifest["mode"] == "PAPER"
    assert manifest["net_result"] == "-0.4300"


def test_replay_rejects_future_leakage():
    book = normalize_orderbook(_load("orderbook.json"), market_id="KXJOBLESS-26JUN18-T250")
    position = simulate_paper_entry(
        forecast=_forecast(),
        orderbook=book,
        requested_contracts=Decimal("1.00"),
    )
    resolution = record_resolution(
        {"market_id": position.market_id},
        "yes",
        "https://example.invalid/result",
        resolved_at=datetime(2020, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError):
        settle_paper_position(position, resolution)
