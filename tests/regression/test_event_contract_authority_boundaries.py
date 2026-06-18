from __future__ import annotations

from foxclaw.adapters import event_contracts as ec
from foxclaw.adapters.event_contracts.dossiers import build_dossier
from foxclaw.adapters.event_contracts.policy import assess_event_contract_policy
from foxclaw.adapters.event_contracts.resolution import assess_resolution_quality


def test_event_contract_package_authority_flags_remain_false():
    assert ec.CAN_SUBMIT_ORDER is False
    assert ec.CAN_MOVE_FUNDS is False
    assert ec.LIVE_EXECUTION_ALLOWED is False
    assert ec.DEFAULT_AUTHORITY_LEVEL == "A4_prohibited"


def test_policy_blocks_paper_when_settlement_source_missing():
    market = {
        "market_id": "KXTEST",
        "title": "Fixture",
        "resolution_rule_text": "Resolves from a public report.",
        "settlement_sources": (),
    }
    dossier = build_dossier(
        market,
        [
            {
                "source_id": "public",
                "title": "Public report",
                "url": "https://example.invalid/report",
                "source_classification": "public",
                "independence_group": "report",
            }
        ],
    )
    verdict = assess_event_contract_policy(
        market_id="KXTEST",
        dossier=dossier,
        resolution_quality=assess_resolution_quality(market),
    )
    assert verdict.can_enter_paper is False
    assert verdict.can_submit_order is False
    assert verdict.can_move_funds is False
    assert verdict.live_execution_allowed is False
    assert "missing_settlement_source" in verdict.reasons


def test_policy_never_lets_rejected_evidence_authorize_action():
    market = {
        "market_id": "KXTEST",
        "title": "Fixture",
        "resolution_rule_text": "Resolves from a public report.",
        "settlement_sources": ("Official | https://example.invalid/source",),
    }
    dossier = build_dossier(
        market,
        [
            {
                "source_id": "insider",
                "title": "Insider message",
                "url": "https://example.invalid/private",
                "source_classification": "insider",
            }
        ],
    )
    verdict = assess_event_contract_policy(
        market_id="KXTEST",
        dossier=dossier,
        resolution_quality=assess_resolution_quality(market),
    )
    assert verdict.can_enter_paper is False
    assert verdict.reasons == ("no_allowed_public_evidence", "some_evidence_rejected")
