from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from foxclaw.adapters.event_contracts.self_funding import evaluate_self_funding

STANDARD = Path(__file__).resolve().parents[2] / "config" / "self_funding_standard.json"


def _standard():
    return json.loads(STANDARD.read_text(encoding="utf-8"))


def test_paper_mode_cannot_make_verified_self_funding_claim():
    report = evaluate_self_funding(
        mode="paper",
        resolved_positions=500,
        consecutive_days=120,
        net_economic_profit=Decimal("500"),
        operating_costs=Decimal("100"),
        standard=_standard(),
    )
    assert report.claim_allowed is False
    assert report.claim_level == "self_funding_candidate"
    assert "mode_not_allowed_for_verified_claim" in report.reasons


def test_missing_costs_prevent_claim():
    report = evaluate_self_funding(
        mode="founder_live",
        resolved_positions=500,
        consecutive_days=120,
        net_economic_profit=Decimal("500"),
        operating_costs=None,
        standard=_standard(),
    )
    assert report.claim_allowed is False
    assert "missing_operating_cost_receipts" in report.reasons


def test_zero_costs_do_not_divide_or_verify():
    report = evaluate_self_funding(
        mode="founder_live",
        resolved_positions=500,
        consecutive_days=120,
        net_economic_profit=Decimal("500"),
        operating_costs=Decimal("0"),
        standard=_standard(),
    )
    assert report.self_funding_ratio is None
    assert report.claim_allowed is False
    assert "zero_operating_costs_cannot_verify_self_funding" in report.reasons


def test_standard_can_pass_only_with_founder_live_receipts():
    report = evaluate_self_funding(
        mode="founder_live",
        resolved_positions=300,
        consecutive_days=100,
        net_economic_profit=Decimal("500"),
        operating_costs=Decimal("100"),
        standard=_standard(),
    )
    assert report.claim_allowed is True
    assert report.self_funding_ratio == Decimal("5")
