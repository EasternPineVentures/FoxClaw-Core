from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from foxclaw.adapters.event_contracts.contracts import ForecastReceipt
from foxclaw.adapters.redshift.paper_boundary import (
    RedshiftPaperExecutionReceipt,
    export_foxclaw_decision,
    rehearse_redshift_paper_execution,
    settle_redshift_paper_execution,
    verify_execution_links_decision,
)


def _forecast() -> ForecastReceipt:
    return ForecastReceipt(
        market_id="KXTEST-RED",
        side="yes",
        verdict="paper",
        independent_probability=Decimal("0.62"),
        market_probability=Decimal("0.43"),
        costs_total=Decimal("0.0200"),
        usable_edge=Decimal("0.1700"),
        minimum_usable_edge=Decimal("0.0500"),
        evidence_quality=Decimal("0.85"),
        dossier_hash="sha256:" + "b" * 64,
        engine_subject="forecast:event_contract:test",
        engine_tier="T2",
        gate_multiplier=Decimal("1.0000"),
        raw_commitment=Decimal("4.0000"),
        adjusted_commitment=Decimal("4.0000"),
        reason="unit fixture",
        code_version="test",
        created_at=datetime(2026, 6, 18, tzinfo=UTC),
    )


def test_redshift_paper_execution_links_to_foxclaw_decision_without_authority():
    decision = export_foxclaw_decision(_forecast())
    execution = rehearse_redshift_paper_execution(
        decision,
        requested_contracts=Decimal("4"),
        fill_price=Decimal("0.45"),
        fees=Decimal("0"),
        slippage=Decimal("0.02"),
        executed_at=datetime(2026, 6, 18, 0, 1, tzinfo=UTC),
    )

    assert verify_execution_links_decision(decision, execution) is True
    assert decision.authority_level == "foxclaw_decision_context_only"
    assert execution.authority_level == "redshift_paper_rehearsal"
    assert execution.redshift_capital_effect == "none"
    assert execution.can_submit_order is False
    assert execution.can_move_funds is False
    assert execution.live_execution_allowed is False
    assert execution.can_mutate_foxclaw_decision is False
    assert execution.live_order_id is None
    assert execution.account_id is None


def test_mutated_decision_snapshot_does_not_verify_against_execution():
    decision = export_foxclaw_decision(_forecast())
    execution = rehearse_redshift_paper_execution(
        decision,
        requested_contracts=Decimal("4"),
        fill_price=Decimal("0.45"),
    )
    mutated = replace(decision, independent_probability=Decimal("0.91"))

    assert verify_execution_links_decision(mutated, execution) is False


def test_redshift_paper_execution_rejects_live_identifiers_or_authority():
    decision = export_foxclaw_decision(_forecast())
    execution = rehearse_redshift_paper_execution(
        decision,
        requested_contracts=Decimal("4"),
        fill_price=Decimal("0.45"),
    )

    with pytest.raises(ValueError, match="live order or account"):
        replace(execution, live_order_id="LIVE-123")
    with pytest.raises(ValueError, match="cannot grant authority"):
        replace(execution, can_submit_order=True)
    with pytest.raises(ValueError, match="capital effect"):
        replace(execution, redshift_capital_effect="paper_profit")


def test_redshift_paper_outcome_returns_result_without_live_authority():
    decision = export_foxclaw_decision(_forecast())
    execution = rehearse_redshift_paper_execution(
        decision,
        requested_contracts=Decimal("4"),
        fill_price=Decimal("0.45"),
        fees=Decimal("0.0100"),
    )
    outcome = settle_redshift_paper_execution(
        execution,
        resolved_outcome="yes",
        settled_at=datetime(2026, 6, 19, tzinfo=UTC),
    )

    assert outcome.payout == Decimal("4.0000")
    assert outcome.entry_cost == Decimal("1.8000")
    assert outcome.net_result == Decimal("2.1900")
    assert outcome.redshift_capital_effect == "none"
    assert outcome.can_submit_order is False
    assert outcome.can_move_funds is False


def test_redshift_receipt_rejects_overfill():
    decision = export_foxclaw_decision(_forecast())
    with pytest.raises(ValueError, match="filled_contracts cannot exceed"):
        rehearse_redshift_paper_execution(
            decision,
            requested_contracts=Decimal("4"),
            filled_contracts=Decimal("5"),
            fill_price=Decimal("0.45"),
        )


def test_execution_receipt_requires_paper_mode():
    decision = export_foxclaw_decision(_forecast())
    execution = rehearse_redshift_paper_execution(
        decision,
        requested_contracts=Decimal("4"),
        fill_price=Decimal("0.45"),
    )
    with pytest.raises(ValueError, match="PAPER mode"):
        RedshiftPaperExecutionReceipt(**{**execution.__dict__, "mode": "LIVE"})
