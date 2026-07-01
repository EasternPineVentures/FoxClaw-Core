from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
INTAKE_FIXTURE = (
    REPO / "tests" / "fixtures" / "coinfox_packet_intake" / "manual_market_pulse_intake.valid.json"
)
PACKET_FIXTURE = REPO / "tests" / "fixtures" / "public_contract" / "coinfox_curated_packet.valid.json"

FORBIDDEN_PUBLIC_FRAGMENTS = (
    "discord.com/channels",
    "discord.gg/",
    "guild_id",
    "channel_id",
    "user_id",
    "message_id",
    "api_key",
    "token=",
    "secret=",
    "password=",
    "webhook",
    "C:\\",
)


def _walk_strings(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)
    elif isinstance(value, str):
        yield value


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def test_curated_packet_intake_fixture_maps_to_public_packet_cards():
    intake = _load(INTAKE_FIXTURE)
    packet = _load(PACKET_FIXTURE)

    assert intake["schema_version"] == "coinfox_curated_packet_intake.v0"
    assert intake["target_packet_type"] == packet["packet_type"] == "market_pulse_now"
    assert intake["expected_public_packet"]["packet_id"] == packet["packet_id"]

    packet_card_ids = {card["card_id"] for card in packet["cards"]}
    observations = intake["source_observations"]
    assert 1 <= len(observations) <= 10
    assert {item["target_card_id"] for item in observations} == packet_card_ids

    for observation in observations:
        assert observation["curation_decision"]["include_in_packet"] is True
        assert observation["curation_decision"]["packet_card_type"] in {
            "market_pulse",
            "idea_prompt",
            "delta",
        }
        assert observation["source"]["source_url"].startswith("https://")
        assert observation["source"]["terms_status"] in {
            "link_only",
            "summary_allowed",
            "aggregate_only",
            "blocked_until_review",
        }
        assert len(observation["corroborations"]) >= 2
        assert observation["source_state"]["trust_state"] in {"quarantined", "trusted"}
        assert observation["source_state"]["can_train_model"] is False
        assert observation["source_state"]["can_update_verified_memory"] is False
        assert observation["safety"]["public_link_only"] is True
        assert observation["safety"]["raw_content_included"] is False
        assert observation["safety"]["contains_private_source_content"] is False
        assert observation["safety"]["contains_credentials"] is False
        assert observation["safety"]["live_execution_allowed"] is False


def test_curated_packet_intake_fixture_has_hard_authority_locks():
    intake = _load(INTAKE_FIXTURE)

    assert intake["authority"]["authority"] == "review_priority_only"
    assert intake["authority"]["can_submit_order"] is False
    assert intake["authority"]["can_move_funds"] is False
    assert intake["authority"]["live_execution_allowed"] is False
    assert intake["authority"]["can_change_truth"] is False
    assert intake["authority"]["can_promote_evidence"] is False
    assert intake["authority"]["can_change_source_reliability"] is False
    assert intake["authority"]["can_authorize_execution"] is False


def test_curated_packet_intake_fixture_does_not_leak_private_fragments():
    intake = _load(INTAKE_FIXTURE)
    blob = "\n".join(_walk_strings(intake)).lower()

    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert fragment.lower() not in blob, f"intake fixture leaked {fragment}"
