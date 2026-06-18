from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from foxclaw.adapters.event_contracts.dossiers import build_dossier
from foxclaw.adapters.event_contracts.kalshi.normalize import normalize_market
from foxclaw.adapters.event_contracts.scoring import assess_forecast
from foxclaw.adapters.event_contracts.storage.repositories import ForecastRepository

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "kalshi"


def _market():
    raw = json.loads((FIXTURES / "market_detail.json").read_text(encoding="utf-8"))["market"]
    return normalize_market(raw)


def _dossier(market):
    return build_dossier(
        market,
        [
            {
                "source_id": "official",
                "title": "Official public release",
                "url": "https://example.invalid/official",
                "source_type": "official",
                "source_classification": "public",
                "independence_group": "official-release",
                "claims": ["Value above threshold"],
            }
        ],
    )


def test_high_probability_at_higher_ask_rejects_yes_edge():
    market = replace(_market(), yes_ask=Decimal("0.9800"), no_ask=None)
    receipt = assess_forecast(
        market=market,
        dossier=_dossier(market),
        independent_probability=Decimal("0.9500"),
    )
    assert receipt.verdict == "reject"
    assert receipt.side == "none"
    assert receipt.usable_edge == Decimal("0")
    assert receipt.can_submit_order is False
    assert receipt.can_move_funds is False
    assert receipt.live_execution_allowed is False


def test_attractive_gap_can_become_paper_candidate():
    market = replace(_market(), yes_ask=Decimal("0.4300"), no_ask=None)
    receipt = assess_forecast(
        market=market,
        dossier=_dossier(market),
        independent_probability=Decimal("0.6200"),
    )
    assert receipt.verdict == "paper"
    assert receipt.side == "yes"
    assert receipt.market_probability == Decimal("0.4300")
    assert receipt.usable_edge == Decimal("0.1900")
    assert receipt.raw_commitment == receipt.usable_edge
    assert receipt.adjusted_commitment == receipt.raw_commitment * receipt.gate_multiplier
    assert receipt.mode == "PAPER"


def test_market_price_never_mutates_independent_probability():
    dossier = _dossier(_market())
    cheap = assess_forecast(
        market=replace(_market(), yes_ask=Decimal("0.4300"), no_ask=None),
        dossier=dossier,
        independent_probability=Decimal("0.6200"),
    )
    expensive = assess_forecast(
        market=replace(_market(), yes_ask=Decimal("0.5000"), no_ask=None),
        dossier=dossier,
        independent_probability=Decimal("0.6200"),
    )
    assert cheap.independent_probability == Decimal("0.6200")
    assert expensive.independent_probability == Decimal("0.6200")
    assert cheap.market_probability != expensive.market_probability


def test_cost_model_can_eliminate_raw_edge():
    market = replace(_market(), yes_ask=Decimal("0.5800"), no_ask=None)
    receipt = assess_forecast(
        market=market,
        dossier=_dossier(market),
        independent_probability=Decimal("0.6200"),
        venue_fee_cost=Decimal("0.0500"),
    )
    assert receipt.verdict == "reject"
    assert receipt.reason == "no_positive_usable_edge"


def test_forecast_receipt_repository_persists_paper_only_result(tmp_path):
    market = replace(_market(), yes_ask=Decimal("0.4300"), no_ask=None)
    receipt = assess_forecast(
        market=market,
        dossier=_dossier(market),
        independent_probability=Decimal("0.6200"),
    )
    repo = ForecastRepository(tmp_path / "forecast_desk.db")
    receipt_id = repo.record_forecast_receipt(receipt)
    with sqlite3.connect(str(repo.db_path)) as conn:
        row = conn.execute(
            "SELECT verdict, mode, usable_edge, receipt_json FROM forecast_receipts WHERE receipt_id = ?",
            (receipt_id,),
        ).fetchone()
    assert row[0] == "paper"
    assert row[1] == "PAPER"
    assert row[2] == "0.1900"
    assert '"can_submit_order":false' in row[3]
