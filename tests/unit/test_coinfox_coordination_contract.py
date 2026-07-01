from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from foxclaw.contract.public import schema_path
from foxclaw.contract.public.coinfox_coordination import (
    blocked_authority_requests,
    build_demo_ledger,
    is_blocked_request,
    validate_coordination_packet,
)
from foxclaw.contract.public.schema_validation import validate_json_schema

REPO = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO / "tests" / "fixtures" / "contracts"
TOOL = REPO / "tools" / "coinfox_coordination_demo.py"

FIXTURES = (
    "coinfox_intent.valid.json",
    "coinfox_decision_ack.valid.json",
    "coinfox_action_receipt.valid.json",
    "coinfox_outcome_receipt.valid.json",
    "coinfox_intent.blocked.json",
    "coinfox_decision_block.valid.json",
)


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_all_coordination_fixtures_validate_against_schema():
    schema = json.loads(schema_path("coinfox_coordination_packet.schema.json").read_text(encoding="utf-8"))

    for fixture_name in FIXTURES:
        packet = _load_fixture(fixture_name)
        validate_json_schema(packet, schema)
        validate_coordination_packet(packet)
        assert packet["schema_version"] == "coinfox_coordination_packet.v0"
        assert packet["classification"]["private_evidence_exported"] is False
        assert packet["classification"]["paper_only"] is True


def test_auto_publish_intent_is_schema_valid_but_policy_blocked():
    packet = _load_fixture("coinfox_intent.blocked.json")

    validate_coordination_packet(packet)
    assert "auto_publish" in packet["authority_requested"]
    assert packet["intent"]["requested_action"] == "auto_publish"
    assert blocked_authority_requests(packet) == ["auto_publish"]
    assert is_blocked_request(packet) is True


def test_draft_only_intent_is_not_policy_blocked():
    packet = _load_fixture("coinfox_intent.valid.json")

    validate_coordination_packet(packet)
    assert packet["authority_requested"] == ["draft_only"]
    assert blocked_authority_requests(packet) == []
    assert is_blocked_request(packet) is False


def test_demo_ledger_generates_exactly_four_packets():
    ledger = build_demo_ledger()

    assert ledger["schema_version"] == "foxclaw_ledger_demo.v0"
    assert ledger["production_writes"] is False
    assert ledger["live_api_calls"] is False
    assert ledger["packet_count"] == 4
    assert [packet["packet_type"] for packet in ledger["packets"]] == [
        "IntentPacket",
        "CoordinationDecision",
        "ActionReceipt",
        "OutcomeReceipt",
    ]
    assert ledger["packets"][1]["decision"] == "ack"
    assert ledger["packets"][2]["action_receipt"]["action_taken"] == "exported_sanitized_cards"
    assert ledger["packets"][3]["outcome_receipt"]["public_engagement"]["comments_count"] == 14


def test_demo_ledger_hash_chain_is_chronological():
    packets = build_demo_ledger()["packets"]
    hashes = [packet["packet_hash"] for packet in packets]

    assert len(hashes) == len(set(hashes)) == 4
    assert all(item.startswith("sha256:") for item in hashes)
    assert packets[0]["previous_packet_hash"] is None
    assert packets[1]["previous_packet_hash"] == packets[0]["packet_hash"]
    assert packets[2]["previous_packet_hash"] == packets[1]["packet_hash"]
    assert packets[3]["previous_packet_hash"] == packets[2]["packet_hash"]


def test_coordination_demo_cli_prints_ledger_json():
    completed = subprocess.run(
        [sys.executable, str(TOOL)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["packet_count"] == 4
    assert payload["packets"][0]["packet_type"] == "IntentPacket"
    assert payload["packets"][-1]["packet_type"] == "OutcomeReceipt"
