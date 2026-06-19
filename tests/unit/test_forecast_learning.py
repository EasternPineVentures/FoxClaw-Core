from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from foxclaw.adapters.event_contracts.contracts import ForecastReceipt
from foxclaw.adapters.event_contracts.learning import build_learning_receipt
from foxclaw.adapters.event_contracts.paper import PaperOutcome


def _forecast(*, side: str = "yes", market_probability: Decimal = Decimal("0.43")):
    return ForecastReceipt(
        market_id="KXLEARN-TEST",
        side=side,
        verdict="paper",
        independent_probability=Decimal("0.62"),
        market_probability=market_probability,
        costs_total=Decimal("0"),
        usable_edge=Decimal("0.19"),
        minimum_usable_edge=Decimal("0.05"),
        evidence_quality=Decimal("0.82"),
        dossier_hash="sha256:" + "b" * 64,
        engine_subject=f"forecast:KXLEARN-TEST:{side}",
        engine_tier="allow",
        gate_multiplier=Decimal("1"),
        raw_commitment=Decimal("0.19"),
        adjusted_commitment=Decimal("0.19"),
        reason="paper_candidate",
        code_version="test",
        created_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
    )


def _outcome(*, resolved_outcome: str = "yes", net_result: Decimal = Decimal("3.99")):
    return PaperOutcome(
        position_id="paper:KXLEARN-TEST:yes:test",
        market_id="KXLEARN-TEST",
        side="yes",
        resolved_outcome=resolved_outcome,
        payout=Decimal("7.00"),
        entry_cost=Decimal("3.01"),
        fees=Decimal("0"),
        net_result=net_result,
        settled_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
    )


def test_learning_receipt_rewards_forecast_that_beats_market_baseline():
    receipt = build_learning_receipt(
        forecast=_forecast(),
        outcome=_outcome(),
        created_at=datetime(2026, 6, 18, 13, 5, tzinfo=UTC),
    )

    assert receipt.learning_receipt_id.startswith("sha256:")
    assert receipt.forecast_brier == Decimal("0.1444")
    assert receipt.market_brier == Decimal("0.3249")
    assert receipt.brier_edge == Decimal("0.1805")
    assert receipt.paper_result_label == "paper_profit"
    assert receipt.decision_quality == "foxclaw_outperformed_market"
    assert receipt.learning_signal == "reinforce"
    assert receipt.public_safe_export_candidate is True
    assert receipt.founder_private_reasoning_excluded is True
    assert receipt.can_set_probability is False
    assert receipt.can_submit_order is False


def test_learning_receipt_converts_no_side_market_probability_to_yes_baseline():
    receipt = build_learning_receipt(
        forecast=_forecast(side="no", market_probability=Decimal("0.70")),
        outcome=_outcome(resolved_outcome="no", net_result=Decimal("-1.00")),
        created_at=datetime(2026, 6, 18, 13, 5, tzinfo=UTC),
    )

    assert receipt.outcome_yes is False
    assert receipt.market_yes_probability == Decimal("0.30")
    assert receipt.paper_result_label == "paper_loss"
    assert receipt.learning_signal == "review"


def test_learning_receipt_rejects_market_mismatch():
    bad_outcome = PaperOutcome(
        position_id="paper:other",
        market_id="OTHER",
        side="yes",
        resolved_outcome="yes",
        payout=Decimal("1"),
        entry_cost=Decimal("0.5"),
        fees=Decimal("0"),
        net_result=Decimal("0.5"),
        settled_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="market_id"):
        build_learning_receipt(forecast=_forecast(), outcome=bad_outcome)
