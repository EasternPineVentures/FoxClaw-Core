"""FoxClaw Ledger V0 receipt models and coordination packet adapter."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any

from foxclaw.contract.public.coinfox_coordination import (
    blocked_authority_requests,
    validate_coordination_packet,
)
from foxclaw.ledger.receipt_hashing import canonical_json, receipt_payload_hash


@dataclass(frozen=True)
class LedgerReceipt:
    receipt_id: str
    receipt_type: str
    source_system: str
    target_system: str
    packet_type: str
    packet_id: str
    intent_id: str
    classification: dict[str, Any]
    authority_requested: list[str]
    authority_granted: list[str]
    status: str
    artifact_refs: list[str]
    input_hash: str
    output_hash: str
    payload_hash: str
    created_at: str
    review_after: str | None
    review_status: str
    safety: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def receipt_from_coordination_packet(packet: dict[str, Any]) -> LedgerReceipt:
    """Convert a Coordination Contract V0 packet into a FoxClaw Ledger receipt."""
    validate_coordination_packet(packet)
    receipt = LedgerReceipt(
        receipt_id=f"fcledger-{packet['packet_id']}",
        receipt_type=_receipt_type(packet["packet_type"]),
        source_system=str(packet["source_system"]),
        target_system=str(packet["target_system"]),
        packet_type=str(packet["packet_type"]),
        packet_id=str(packet["packet_id"]),
        intent_id=str(packet["correlation_id"]),
        classification=dict(packet["classification"]),
        authority_requested=list(packet.get("authority_requested", [])),
        authority_granted=list(packet.get("authority_granted", [])),
        status=_status(packet),
        artifact_refs=_artifact_refs(packet),
        input_hash=_input_hash(packet),
        output_hash=_output_hash(packet),
        payload_hash="",
        created_at=str(packet["created_at"]),
        review_after=_review_after(packet),
        review_status=_review_status(packet),
        safety=_safety_flags(),
    )
    payload = receipt.to_dict()
    return LedgerReceipt(**{**payload, "payload_hash": receipt_payload_hash(payload)})


def _receipt_type(packet_type: str) -> str:
    return {
        "IntentPacket": "coordination_intent",
        "CoordinationDecision": "coordination_decision",
        "ActionReceipt": "coordination_action_receipt",
        "OutcomeReceipt": "coordination_outcome_receipt",
    }[packet_type]


def _status(packet: dict[str, Any]) -> str:
    packet_type = packet["packet_type"]
    if packet_type == "IntentPacket":
        return "blocked" if blocked_authority_requests(packet) else "intent_recorded"
    if packet_type == "CoordinationDecision":
        return "acknowledged" if packet["decision"] == "ack" else "blocked"
    if packet_type == "ActionReceipt":
        return str(packet["action_receipt"]["action_status"])
    if packet_type == "OutcomeReceipt":
        return str(packet["outcome_receipt"]["outcome_status"])
    raise ValueError(f"unsupported coordination packet type: {packet_type}")


def _artifact_refs(packet: dict[str, Any]) -> list[str]:
    packet_type = packet["packet_type"]
    if packet_type == "IntentPacket":
        return list(packet["intent"].get("public_receipt_refs", []))
    if packet_type == "ActionReceipt":
        return list(packet["action_receipt"].get("artifact_refs", []))
    if packet_type == "OutcomeReceipt":
        return list(packet["outcome_receipt"].get("public_links", []))
    return []


def _input_hash(packet: dict[str, Any]) -> str:
    previous = packet.get("previous_packet_hash")
    return previous if isinstance(previous, str) else "sha256:none"


def _output_hash(packet: dict[str, Any]) -> str:
    material = {
        "packet_hash": packet["packet_hash"],
        "packet_type": packet["packet_type"],
        "status": _status(packet),
        "artifact_refs": _artifact_refs(packet),
    }
    return "sha256:" + hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def _review_after(packet: dict[str, Any]) -> str | None:
    if packet["packet_type"] != "OutcomeReceipt":
        return None
    outcome = packet["outcome_receipt"]
    value = outcome.get("review_after")
    return str(value) if value else None


def _review_status(packet: dict[str, Any]) -> str:
    if packet["packet_type"] != "OutcomeReceipt":
        return "not_required"
    outcome = packet["outcome_receipt"]
    if outcome.get("needs_review") or outcome.get("review_after"):
        return "pending"
    if outcome.get("outcome_status") == "review_needed":
        return "pending"
    return "not_required"


def _safety_flags() -> dict[str, bool]:
    return {
        "can_submit_order": False,
        "can_move_funds": False,
        "live_execution_allowed": False,
        "can_publish_to_coinfox": False,
        "can_export_private_evidence": False,
        "can_call_live_coinfox_api": False,
        "can_provide_financial_advice": False,
        "can_real_lending": False,
    }
