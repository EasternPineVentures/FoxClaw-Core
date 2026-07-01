"""Apollo 1 standalone intake continuity reporting.

This module describes what FoxClaw Core can safely run from A1 while A2 and the legacy
Discord parser are unavailable. It reports operator lanes; it does not connect sources,
fetch feeds, publish to CoinFox, or mutate authority.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST = Path(__file__).resolve().parent.parent / "config" / "apollo1_intake_lanes.json"
ALLOWED_STATUSES = {"ready", "practice", "planned", "deferred", "blocked"}
DANGEROUS_PROOF_COMMAND_FRAGMENTS = (
    ".env",
    "--live",
    "--rekey",
    "rekey ",
    "secret",
    "wallet",
    "move-funds",
    "move_funds",
    "submit-order",
    "submit_order",
)
AUTHORITY_KEYS = (
    "can_submit_order",
    "can_move_funds",
    "live_execution_allowed",
    "can_publish_to_coinfox",
    "can_change_source_reliability",
    "can_update_verified_memory",
)


@dataclass(frozen=True)
class Apollo1IntakeLane:
    id: str
    name: str
    status: str
    required_for_a1_continuity: bool
    ready_without_a2: bool
    apollo2_required: bool
    source_mode: str
    purpose: str
    operator_action: str
    proof_command: str
    safety_boundary: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Apollo1IntakeLane":
        missing = {
            "id",
            "name",
            "status",
            "required_for_a1_continuity",
            "ready_without_a2",
            "apollo2_required",
            "source_mode",
            "purpose",
            "operator_action",
            "proof_command",
            "safety_boundary",
        } - set(payload)
        if missing:
            raise ValueError(f"apollo1 intake lane missing required fields: {sorted(missing)}")

        status = str(payload["status"])
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"unknown apollo1 intake lane status: {status}")
        proof_command = str(payload["proof_command"])
        lowered_command = proof_command.lower()
        for fragment in DANGEROUS_PROOF_COMMAND_FRAGMENTS:
            if fragment in lowered_command:
                raise ValueError(
                    f"apollo1 intake proof command for {payload['id']} "
                    f"contains unsafe fragment: {fragment}"
                )

        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            status=status,
            required_for_a1_continuity=bool(payload["required_for_a1_continuity"]),
            ready_without_a2=bool(payload["ready_without_a2"]),
            apollo2_required=bool(payload["apollo2_required"]),
            source_mode=str(payload["source_mode"]),
            purpose=str(payload["purpose"]),
            operator_action=str(payload["operator_action"]),
            proof_command=proof_command,
            safety_boundary=str(payload["safety_boundary"]),
        )


def load_manifest(path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "apollo1_intake_lanes.v0":
        raise ValueError("apollo1 intake manifest must use schema_version apollo1_intake_lanes.v0")
    _validate_authority(manifest.get("authority", {}))
    lanes = [Apollo1IntakeLane.from_dict(item) for item in manifest.get("lanes", [])]
    if not lanes:
        raise ValueError("apollo1 intake manifest must contain at least one lane")
    manifest["lanes"] = lanes
    return manifest


def build_report(
    path: str | Path = DEFAULT_MANIFEST,
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(path)
    lanes: list[Apollo1IntakeLane] = manifest["lanes"]
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0)
    counts = Counter(lane.status for lane in lanes)
    required = [lane for lane in lanes if lane.required_for_a1_continuity]
    required_not_ready = [lane for lane in required if lane.status != "ready" or not lane.ready_without_a2]
    blocked = [lane for lane in lanes if lane.status == "blocked"]
    deferred_to_a2 = [lane for lane in lanes if lane.apollo2_required]
    a1_ready = not required_not_ready and not blocked

    return {
        "schema_version": "apollo1_intake_report.v0",
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "generated_for": manifest["generated_for"],
        "readiness_status": "a1_continuity_ready" if a1_ready else "needs_attention",
        "authority": manifest["authority"],
        "counts": {status: counts.get(status, 0) for status in sorted(ALLOWED_STATUSES)},
        "required_for_a1_continuity": {
            "total": len(required),
            "ready": len(required) - len(required_not_ready),
            "not_ready": len(required_not_ready),
        },
        "blocked": [_lane_summary(lane) for lane in blocked],
        "deferred_to_a2": [_lane_summary(lane) for lane in deferred_to_a2],
        "a1_ready_lanes": [
            _lane_summary(lane)
            for lane in lanes
            if lane.ready_without_a2 and lane.status in {"ready", "practice", "planned"}
        ],
        "next_actions": [
            _lane_summary(lane)
            for lane in lanes
            if lane.required_for_a1_continuity or lane.status in {"practice", "planned"}
        ],
        "lanes": [_lane_summary(lane) for lane in lanes],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Apollo 1 Standalone Intake",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Readiness: `{report['readiness_status']}`",
        "",
        "## A1 Continuity",
        "",
        f"- Required ready: `{report['required_for_a1_continuity']['ready']}` / "
        f"`{report['required_for_a1_continuity']['total']}`",
        f"- Required not ready: `{report['required_for_a1_continuity']['not_ready']}`",
        f"- Blocked lanes: `{len(report['blocked'])}`",
        f"- Deferred to A2: `{len(report['deferred_to_a2'])}`",
        "",
        "## Ready On A1",
        "",
    ]
    for item in report["a1_ready_lanes"]:
        lines.append(
            f"- `{item['id']}` ({item['status']}): {item['operator_action']}"
        )
    lines.extend(["", "## Deferred To A2", ""])
    for item in report["deferred_to_a2"]:
        lines.append(
            f"- `{item['id']}` ({item['status']}): {item['operator_action']}"
        )
    lines.extend(
        [
            "",
            "## Proof Commands",
            "",
        ]
    )
    for item in report["next_actions"]:
        lines.append(f"- `{item['id']}`: `{item['proof_command']}`")
    lines.extend(
        [
            "",
            "## Authority",
            "",
            "- `can_submit_order=false`",
            "- `can_move_funds=false`",
            "- `live_execution_allowed=false`",
            "- `can_publish_to_coinfox=false`",
            "- `can_change_source_reliability=false`",
            "- `can_update_verified_memory=false`",
            "",
        ]
    )
    return "\n".join(lines)


def _lane_summary(lane: Apollo1IntakeLane) -> dict[str, Any]:
    return {
        "id": lane.id,
        "name": lane.name,
        "status": lane.status,
        "required_for_a1_continuity": lane.required_for_a1_continuity,
        "ready_without_a2": lane.ready_without_a2,
        "apollo2_required": lane.apollo2_required,
        "source_mode": lane.source_mode,
        "purpose": lane.purpose,
        "operator_action": lane.operator_action,
        "proof_command": lane.proof_command,
        "safety_boundary": lane.safety_boundary,
    }


def _validate_authority(authority: dict[str, Any]) -> None:
    for key in AUTHORITY_KEYS:
        if authority.get(key) is not False:
            raise ValueError(f"apollo1 intake authority must keep {key}=false")
