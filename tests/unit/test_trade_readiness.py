from __future__ import annotations

from foxclaw.adapters.market.risk_labels import classify_market_risk
from foxclaw.adapters.market.tradeability import MarketTradeabilityInput, build_tradeability_snapshot
from foxclaw.engine.information_quality import InformationQualityInput, assess_information_quality
from foxclaw.engine.readiness import (
    GOOD_SIGNAL_BAD_TRADE,
    PLAN_NOT_PLANNED,
    PLAN_PAPER_READY,
    RISK_REDLINE,
    RISK_STRUCTURED,
    STRUCTURED_READY,
    ReadinessInput,
    assess_trade_readiness,
)
from foxclaw.policy.readiness import evaluate_public_trade_idea_readiness


def test_good_signal_bad_trade_keeps_separate_scores():
    verdict = assess_trade_readiness(
        ReadinessInput(
            attention=94,
            evidence_quality=79,
            signal_confidence=84,
            cost_adjusted_edge=11,
            tradeability=31,
            entry_quality=22,
            risk=92,
            plan_readiness=0,
            source_track_record=63,
            setup_track_record=58,
        )
    )
    assert verdict.verdict == GOOD_SIGNAL_BAD_TRADE
    assert verdict.risk_class == RISK_REDLINE
    assert verdict.plan_readiness == PLAN_NOT_PLANNED
    assert verdict.can_present_as_trade_idea is False
    assert verdict.scores["signal_confidence"] == 84
    assert verdict.scores["tradeability"] == 31
    assert verdict.scores["entry_quality"] == 22
    assert "good_signal_bad_trade" in verdict.reason_codes
    assert "better entry" in verdict.professional_wait_for


def test_structured_readiness_can_be_presented_for_paper_review():
    verdict = assess_trade_readiness(
        ReadinessInput(
            attention=62,
            evidence_quality=78,
            signal_confidence=73,
            cost_adjusted_edge=9,
            tradeability=74,
            entry_quality=76,
            risk=42,
            plan_readiness=84,
            source_track_record=68,
            setup_track_record=71,
        )
    )
    assert verdict.verdict == STRUCTURED_READY
    assert verdict.risk_class == RISK_STRUCTURED
    assert verdict.plan_readiness == PLAN_PAPER_READY
    assert verdict.can_present_as_trade_idea is True
    policy = evaluate_public_trade_idea_readiness(verdict.__dict__)
    assert policy.allowed is True


def test_signal_cannot_be_public_trade_idea_without_readiness_verdict():
    missing = evaluate_public_trade_idea_readiness(None)
    assert missing.allowed is False
    assert missing.reason_codes == ("missing_readiness_verdict",)

    verdict = assess_trade_readiness(
        ReadinessInput(
            attention=90,
            evidence_quality=80,
            signal_confidence=82,
            cost_adjusted_edge=8,
            tradeability=30,
            entry_quality=25,
            risk=90,
            plan_readiness=10,
            source_track_record=60,
            setup_track_record=60,
        )
    )
    policy = evaluate_public_trade_idea_readiness(verdict.__dict__)
    assert policy.allowed is False
    assert "risk_class_blocks_trade_idea" in policy.reason_codes
    assert "plan_not_paper_ready" in policy.reason_codes


def test_market_tradeability_snapshot_feeds_readiness_dimensions():
    snapshot = build_tradeability_snapshot(
        MarketTradeabilityInput(
            liquidity=70,
            spread_quality=35,
            slippage_risk=72,
            timing_quality=40,
            entry_quality=28,
        )
    )
    assert snapshot.status == "poor"
    assert snapshot.tradeability <= 45
    assert snapshot.entry_quality == 28
    assert "wide_spread" in snapshot.reason_codes
    assert "poor_entry_quality" in snapshot.reason_codes


def test_information_quality_preserves_component_scores():
    verdict = assess_information_quality(
        InformationQualityInput(
            source_independence=80,
            traceability=75,
            freshness=90,
            corroboration=70,
            contradiction_penalty=30,
        )
    )
    assert verdict.evidence_quality == 68
    assert verdict.source_independence == 80
    assert verdict.traceability == 75
    assert verdict.freshness == 90
    assert verdict.corroboration == 70


def test_market_risk_labels_use_shared_vocabulary():
    assert classify_market_risk(risk_score=88, plan_ready=True, tradeable=True) == RISK_REDLINE
    assert classify_market_risk(risk_score=35, plan_ready=True, tradeable=True) == RISK_STRUCTURED
