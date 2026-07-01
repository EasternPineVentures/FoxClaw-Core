"""FoxClaw-CoinFox coordination contract V0 helpers.

This module is contract/demo support only. It does not call CoinFox, publish content,
read private evidence, place orders, route orders, hold funds, or write production state.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from foxclaw.contract.public import schema_path
from foxclaw.contract.public.schema_validation import validate_json_schema

COORDINATION_SCHEMA = schema_path("coinfox_coordination_packet.schema.json")
CONTRACT_VERSION = "1.0.0"
SCHEMA_VERSION = "coinfox_coordination_packet.v0"

BLOCKED_AUTHORITIES = frozenset(
    {
        "auto_publish",
        "place_order",
        "route_order",
        "hold_funds",
        "provide_financial_advice",
        "real_lending",
    }
)
BLOCKED_ACTIONS = frozenset(
    {
        "auto_publish",
        "place_order",
        "route_order",
        "hold_funds",
        "provide_financial_advice",
        "real_lending",
    }
)


def load_coordination_schema(path: str | Path = COORDINATION_SCHEMA) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_coordination_packet(packet: dict[str, Any]) -> None:
    validate_json_schema(packet, load_coordination_schema())


def packet_hash(packet: dict[str, Any]) -> str:
    payload = deepcopy(packet)
    payload["packet_hash"] = ""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def attach_packet_hash(packet: dict[str, Any]) -> dict[str, Any]:
    hashed = deepcopy(packet)
    hashed["packet_hash"] = packet_hash(hashed)
    return hashed


def blocked_authority_requests(packet: dict[str, Any]) -> list[str]:
    requested = set(packet.get("authority_requested", []))
    intent = packet.get("intent", {})
    requested_action = intent.get("requested_action")
    blocked = set(requested & BLOCKED_AUTHORITIES)
    if requested_action in BLOCKED_ACTIONS:
        blocked.add(str(requested_action))
    return sorted(blocked)


def is_blocked_request(packet: dict[str, Any]) -> bool:
    return bool(blocked_authority_requests(packet))


def build_demo_ledger() -> dict[str, Any]:
    """Build the four-packet happy path as an in-memory FoxClaw Ledger demo."""
    log: list[dict[str, Any]] = []

    intent = _base_packet(
        packet_type="IntentPacket",
        packet_id="coord-demo-intent-001",
        correlation_id="coord-demo-flow-001",
        sequence=1,
        created_at="2026-07-01T16:00:00Z",
        source_system="foxclaw",
        target_system="coinfox",
        previous_packet_hash=None,
        authority_requested=["draft_only"],
        authority_granted=[],
    )
    intent["intent"] = {
        "requested_action": "prepare_draft_cards",
        "why_now": "FoxClaw has public-safe market pulse candidates ready for draft review.",
        "expected_output": "draft_cards",
        "public_safe_summary": "Prepare draft-only CoinFox cards from sanitized public packet candidates.",
        "public_receipt_refs": ["tests/fixtures/public_contract/coinfox_curated_packet.valid.json"],
        "private_evidence_refs": [],
        "expires_at": "2026-07-01T18:00:00Z",
        "risk_flags": ["no_auto_publish", "public_safe_only"],
    }
    _append_valid_packet(log, intent)

    decision = _base_packet(
        packet_type="CoordinationDecision",
        packet_id="coord-demo-decision-ack-001",
        correlation_id="coord-demo-flow-001",
        sequence=2,
        created_at="2026-07-01T16:01:00Z",
        source_system="coinfox",
        target_system="foxclaw",
        previous_packet_hash=log[-1]["packet_hash"],
        authority_requested=["draft_only"],
        authority_granted=["draft_only"],
    )
    decision["decision"] = "ack"
    decision["coordination_decision"] = {
        "decision_reason": "CoinFox accepts draft-only sanitized card preparation.",
        "allowed_next_action": "export_sanitized_cards",
        "blocked_authority": [],
        "safe_next_step": "FoxClaw may emit an ActionReceipt after exporting sanitized draft cards.",
    }
    _append_valid_packet(log, decision)

    action_receipt = _base_packet(
        packet_type="ActionReceipt",
        packet_id="coord-demo-action-receipt-001",
        correlation_id="coord-demo-flow-001",
        sequence=3,
        created_at="2026-07-01T16:02:00Z",
        source_system="foxclaw",
        target_system="coinfox",
        previous_packet_hash=log[-1]["packet_hash"],
        authority_requested=["draft_only"],
        authority_granted=["draft_only"],
    )
    action_receipt["action_receipt"] = {
        "action_status": "executed",
        "action_taken": "exported_sanitized_cards",
        "matched_intent": True,
        "summary": "FoxClaw exported sanitized draft cards for CoinFox review only.",
        "artifact_refs": ["coinfox-draft-card-demo-001"],
        "block_reason": "",
    }
    _append_valid_packet(log, action_receipt)

    outcome_receipt = _base_packet(
        packet_type="OutcomeReceipt",
        packet_id="coord-demo-outcome-receipt-001",
        correlation_id="coord-demo-flow-001",
        sequence=4,
        created_at="2026-07-01T17:30:00Z",
        source_system="coinfox",
        target_system="foxclaw",
        previous_packet_hash=log[-1]["packet_hash"],
        authority_requested=["return_public_engagement_receipts", "outcome_review"],
        authority_granted=["return_public_engagement_receipts"],
    )
    outcome_receipt["outcome_receipt"] = {
        "outcome_status": "review_needed",
        "public_engagement": {
            "comments_count": 14,
            "challenges_count": 3,
            "saves_count": 8,
            "votes_count": 21,
        },
        "public_links": ["coinfox://draft/coinfox-draft-card-demo-001"],
        "outcome_summary": (
            "Draft cards produced useful public discussion and several challenges for later review."
        ),
        "return_to_foxclaw": [
            "review_aging_thesis",
            "compare_challenges",
            "no_memory_write_in_demo",
        ],
    }
    _append_valid_packet(log, outcome_receipt)

    return {
        "schema_version": "foxclaw_ledger_demo.v0",
        "generated_at": datetime(2026, 7, 1, 17, 31, tzinfo=UTC)
        .isoformat()
        .replace("+00:00", "Z"),
        "ledger_name": "FoxClaw Ledger coordination demo",
        "production_writes": False,
        "live_api_calls": False,
        "packet_count": len(log),
        "packets": log,
    }


def _base_packet(
    *,
    packet_type: str,
    packet_id: str,
    correlation_id: str,
    sequence: int,
    created_at: str,
    source_system: str,
    target_system: str,
    previous_packet_hash: str | None,
    authority_requested: list[str],
    authority_granted: list[str],
) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "packet_type": packet_type,
        "packet_id": packet_id,
        "packet_hash": "",
        "correlation_id": correlation_id,
        "sequence": sequence,
        "created_at": created_at,
        "source_system": source_system,
        "target_system": target_system,
        "previous_packet_hash": previous_packet_hash,
        "classification": {
            "data_classification": "public_safe_coordination",
            "public_safe": True,
            "private_evidence_exported": False,
            "paper_only": True,
            "no_trading": True,
            "no_custody": True,
            "not_financial_advice": True,
            "not_real_lending": True,
        },
        "authority_requested": authority_requested,
        "authority_granted": authority_granted,
    }


def _append_valid_packet(log: list[dict[str, Any]], packet: dict[str, Any]) -> None:
    hashed = attach_packet_hash(packet)
    validate_coordination_packet(hashed)
    log.append(hashed)
