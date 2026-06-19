from __future__ import annotations

import pytest

from foxclaw.adapters.market.candidate_projection import (
    CandidatePayloadDecodeError,
    CandidatePayloadTypeError,
    project_candidate,
)


def _record(payload: str) -> dict[str, object]:
    return {
        "candidate_id": 7,
        "candidate_uid": "cand_fixture_7",
        "receipt_id": "candidate_fixture_7",
        "event_id": 70,
        "attempt_id": 700,
        "source_id": "private_source_alpha",
        "source_type": "discord",
        "parser_version": "parser_v_fixture",
        "candidate_type": "trade_signal",
        "normalized_payload_json": payload,
        "confidence": 0.99,
        "admission_policy_version": "accepted_candidate_v0",
        "admission_reason": "fixture",
        "status": "accepted",
        "created_at": "2026-06-19T18:00:00+00:00",
        "evidence_hash": "sha256:candidatefixture7",
    }


def test_projection_preserves_explicit_payload_values_only() -> None:
    projection = project_candidate(
        _record(
            """
            {
              "candidate_type": "trade_signal",
              "subject": "BTC/USD thesis",
              "symbol": "BTC/USD",
              "direction_or_outcome": "up",
              "side": "long",
              "summary": "Momentum claim with explicit plan fields.",
              "time_horizon": "hours",
              "entry_price": 100.5,
              "stop_loss": 95.0,
              "take_profit": 110.0
            }
            """
        )
    )

    assert projection.candidate_type == "trade_signal"
    assert projection.subject == "BTC/USD thesis"
    assert projection.symbol == "BTC/USD"
    assert projection.direction_or_outcome == "up"
    assert projection.side == "long"
    assert projection.summary == "Momentum claim with explicit plan fields."
    assert projection.time_horizon == "hours"
    assert projection.entry_price == 100.5
    assert projection.stop_loss == 95.0
    assert projection.take_profit == 110.0
    assert projection.internal_lineage["candidate_id"] == 7


def test_projection_does_not_invent_targets_or_timeframe_aliases() -> None:
    projection = project_candidate(
        _record(
            """
            {
              "candidate_type": "trade_signal",
              "symbol": "ETH/USD",
              "side": "long",
              "summary": "Summary says entry 100 stop 90 target 130 next week.",
              "time_horizon": "days",
              "take_profit": 130
            }
            """
        )
    )

    assert projection.take_profit == 130
    assert not hasattr(projection, "targets")
    assert not hasattr(projection, "timeframe")
    assert projection.entry_price is None
    assert projection.stop_loss is None


def test_summary_only_candidate_remains_assessable_with_missing_fields() -> None:
    projection = project_candidate(
        _record('{"candidate_type":"market_news","summary":"Watch-only fixture."}')
    )

    assert projection.candidate_type == "market_news"
    assert projection.summary == "Watch-only fixture."
    assert projection.symbol is None
    assert projection.side is None
    assert "symbol" in projection.missing_fields
    assert "side" in projection.missing_fields


def test_malformed_json_raises_focused_decode_error() -> None:
    with pytest.raises(CandidatePayloadDecodeError):
        project_candidate(_record('{"candidate_type":'))


@pytest.mark.parametrize("payload", ["[]", '"text"', "null"])
def test_valid_non_object_payload_raises_focused_type_error(payload: str) -> None:
    with pytest.raises(CandidatePayloadTypeError):
        project_candidate(_record(payload))


def test_parser_confidence_is_preserved_only_as_internal_parser_confidence() -> None:
    projection = project_candidate(
        _record('{"candidate_type":"trade_signal","summary":"Strong parser confidence."}')
    )

    assert projection.parser_confidence == 0.99
    assert "risk" not in projection.public_fields
    assert "edge" not in projection.public_fields
