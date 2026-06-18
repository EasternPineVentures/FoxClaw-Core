from __future__ import annotations

from datetime import UTC, datetime

import pytest

from foxclaw.adapters.event_contracts.resolution import (
    assess_resolution_quality,
    record_resolution,
)


def test_resolution_quality_blocks_missing_settlement_source():
    verdict = assess_resolution_quality(
        {
            "market_id": "KXTEST",
            "resolution_rule_text": "Resolves from a public release.",
            "settlement_sources": (),
        }
    )
    assert verdict.blocks_paper_entry is True
    assert "missing_settlement_source" in verdict.reasons


def test_resolution_quality_is_clear_when_rule_and_source_exist():
    verdict = assess_resolution_quality(
        {
            "market_id": "KXTEST",
            "resolution_rule_text": "Resolves from a public release.",
            "settlement_sources": ("Official | https://example.invalid/source",),
        }
    )
    assert verdict.blocks_paper_entry is False
    assert verdict.clarity_score == 1


def test_record_resolution_is_public_read_only_receipt():
    receipt = record_resolution(
        {"market_id": "KXTEST"},
        "yes",
        "https://example.invalid/result",
        resolved_at=datetime(2026, 6, 18, tzinfo=UTC),
    )
    assert receipt.resolved_outcome == "yes"
    assert receipt.public_information_only is True
    assert receipt.can_submit_order is False
    assert receipt.can_move_funds is False


def test_record_resolution_rejects_bad_outcome_or_private_url():
    with pytest.raises(ValueError):
        record_resolution({"market_id": "KXTEST"}, "maybe", "https://example.invalid/result")
    with pytest.raises(ValueError):
        record_resolution({"market_id": "KXTEST"}, "yes", "file://private")
