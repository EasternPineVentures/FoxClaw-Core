from __future__ import annotations

from datetime import UTC, datetime

import pytest

from foxclaw.adapters.event_contracts.dossiers import build_dossier
from foxclaw.adapters.event_contracts.intake import (
    SUBMIT_EVIDENCE_CAPABILITY,
    TrustedSubmitter,
    packet_to_dossier_evidence,
    submit_evidence_packet,
    validate_evidence_packet,
)


def _submitter(*, active: bool = True, capabilities: tuple[str, ...] | None = None):
    return TrustedSubmitter(
        submitter_id="trusted-analyst",
        display_name="Trusted Analyst",
        trust_tier="trusted_analyst",
        capabilities=capabilities if capabilities is not None else (SUBMIT_EVIDENCE_CAPABILITY,),
        active=active,
    )


def _raw():
    return {
        "market_id": "KXTEST",
        "source_id": "official-report",
        "title": "Official report",
        "url": "https://example.invalid/report",
        "source_type": "official",
        "source_classification": "public",
        "independence_group": "official-report",
        "claims": ["Official public report says the threshold was reached."],
    }


def test_trusted_submitter_can_submit_context_only_public_evidence():
    packet = submit_evidence_packet(
        _submitter(),
        _raw(),
        submitted_at=datetime(2026, 6, 18, tzinfo=UTC),
    )
    validation = validate_evidence_packet(packet)
    dossier = build_dossier(
        {
            "market_id": "KXTEST",
            "title": "Fixture market",
            "resolution_rule_text": "Resolves from a public report.",
            "settlement_sources": ("Official | https://example.invalid/source",),
        },
        [packet_to_dossier_evidence(packet)],
    )

    assert packet.status == "pending_review"
    assert packet.authority_level == "context_only"
    assert packet.can_set_probability is False
    assert packet.can_publish is False
    assert packet.can_enter_paper is False
    assert packet.can_submit_order is False
    assert packet.can_move_funds is False
    assert packet.live_execution_allowed is False
    assert validation.status == "accepted"
    assert validation.accepted_for_dossier is True
    assert validation.can_authorize_execution is False
    assert len(dossier.evidence) == 1


def test_inactive_or_uncapable_submitters_are_rejected():
    with pytest.raises(PermissionError):
        submit_evidence_packet(_submitter(active=False), _raw())
    with pytest.raises(PermissionError):
        submit_evidence_packet(_submitter(capabilities=()), _raw())


def test_trusted_intake_rejects_probability_or_authority_attempts():
    raw = _raw() | {"independent_probability": "0.91"}
    with pytest.raises(ValueError, match="authority fields"):
        submit_evidence_packet(_submitter(), raw)

    raw = _raw() | {"can_publish": False}
    with pytest.raises(ValueError, match="authority fields"):
        submit_evidence_packet(_submitter(), raw)


def test_nonpublic_packet_is_stored_as_context_but_fails_validation():
    packet = submit_evidence_packet(
        _submitter(),
        _raw() | {"source_classification": "insider", "public": True},
    )
    validation = validate_evidence_packet(packet)

    assert validation.status == "rejected"
    assert validation.accepted_for_dossier is False
    assert validation.public_information_only is False
    assert "insider" in validation.reasons[0]


def test_duplicate_independence_group_is_not_added_to_dossier_queue():
    packet = submit_evidence_packet(_submitter(), _raw())
    validation = validate_evidence_packet(
        packet,
        seen_duplicate_keys=(packet.independence_group,),
    )

    assert validation.status == "duplicate"
    assert validation.accepted_for_dossier is False
    assert validation.reasons == ("duplicate_independence_group",)


def test_submitter_cannot_be_created_with_execution_authority():
    with pytest.raises(ValueError, match="cannot carry execution"):
        TrustedSubmitter(
            submitter_id="bad",
            display_name="Bad",
            trust_tier="trusted_analyst",
            capabilities=(SUBMIT_EVIDENCE_CAPABILITY,),
            can_submit_order=True,
        )
