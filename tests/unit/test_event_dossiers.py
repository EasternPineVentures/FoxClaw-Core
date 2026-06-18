from __future__ import annotations

from foxclaw.adapters.event_contracts.dossiers import (
    assess_evidence_eligibility,
    build_dossier,
)


def _market():
    return {
        "market_id": "KXTEST",
        "title": "Fixture market",
        "resolution_rule_text": "Resolves from the official public release.",
        "settlement_sources": ("Official source | https://example.invalid/source",),
    }


def test_nonpublic_evidence_is_rejected_at_intake():
    verdict = assess_evidence_eligibility(
        {
            "source_id": "private-chat",
            "url": "https://example.invalid/private",
            "source_classification": "material_nonpublic",
            "public": True,
        }
    )
    assert verdict.allowed is False
    assert verdict.public_information_only is False


def test_llm_or_prose_cannot_override_banned_classification():
    verdict = assess_evidence_eligibility(
        {
            "source_id": "leak",
            "url": "https://example.invalid/leak",
            "source_classification": "hacked",
            "llm_says_public": True,
        }
    )
    assert verdict.allowed is False
    assert "hacked" in verdict.reason


def test_dossier_collapses_duplicate_independence_group_and_hash_is_stable():
    evidence = [
        {
            "source_id": "official-a",
            "title": "Official release",
            "url": "https://example.invalid/official",
            "source_type": "official",
            "source_classification": "public",
            "independence_group": "official-release",
            "claims": ["Value above threshold"],
        },
        {
            "source_id": "wire-repeat",
            "title": "Wire repeats official release",
            "url": "https://example.invalid/wire",
            "source_type": "news",
            "source_classification": "public",
            "independence_group": "official-release",
            "claims": ["Value above threshold"],
        },
    ]
    first = build_dossier(_market(), evidence)
    second = build_dossier(_market(), evidence)
    assert first.independence_group_count == 1
    assert first.duplicate_evidence_collapsed == 1
    assert len(first.evidence) == 1
    assert first.dossier_hash == second.dossier_hash
    assert first.can_authorize_execution is False
    assert first.can_execute_trades is False


def test_dossier_records_rejected_evidence_without_using_it():
    dossier = build_dossier(
        _market(),
        [
            {
                "source_id": "ok",
                "title": "Public source",
                "url": "https://example.invalid/public",
                "source_classification": "public",
                "independence_group": "public-source",
            },
            {
                "source_id": "insider",
                "title": "Insider note",
                "url": "https://example.invalid/insider",
                "source_classification": "insider",
            },
        ],
    )
    assert len(dossier.evidence) == 1
    assert len(dossier.rejected_evidence) == 1
    assert dossier.rejected_evidence[0].allowed is False
