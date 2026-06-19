"""FoxClaw Gym readiness reporting.

The gym is a demo-readiness and practice surface. It reports direction, proof
commands, and next-attention items without executing live authority.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST = Path(__file__).resolve().parent.parent / "config" / "foxclaw_gym_drills.json"
ALLOWED_STATUSES = {"ready", "practice", "scaffold", "planned", "blocked"}
ATTENTION_STATUSES = {"practice", "scaffold", "planned", "blocked"}
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


@dataclass(frozen=True)
class GymDrill:
    id: str
    name: str
    lane: str
    status: str
    demo_critical: bool
    attention_rank: int
    due_date: str
    purpose: str
    proof_command: str
    demo_line: str
    next_action: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GymDrill":
        missing = {
            "id",
            "name",
            "lane",
            "status",
            "demo_critical",
            "attention_rank",
            "due_date",
            "purpose",
            "proof_command",
            "demo_line",
            "next_action",
        } - set(payload)
        if missing:
            raise ValueError(f"gym drill missing required fields: {sorted(missing)}")
        status = str(payload["status"])
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"unknown gym drill status: {status}")
        proof_command = str(payload["proof_command"])
        lowered_command = proof_command.lower()
        for fragment in DANGEROUS_PROOF_COMMAND_FRAGMENTS:
            if fragment in lowered_command:
                raise ValueError(
                    f"gym proof command for {payload['id']} contains unsafe fragment: {fragment}"
                )
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            lane=str(payload["lane"]),
            status=status,
            demo_critical=bool(payload["demo_critical"]),
            attention_rank=int(payload["attention_rank"]),
            due_date=str(payload["due_date"]),
            purpose=str(payload["purpose"]),
            proof_command=proof_command,
            demo_line=str(payload["demo_line"]),
            next_action=str(payload["next_action"]),
        )


def load_manifest(path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_authority(manifest.get("authority", {}))
    drills = [GymDrill.from_dict(item) for item in manifest.get("drills", [])]
    if not drills:
        raise ValueError("gym manifest must contain at least one drill")
    manifest["drills"] = drills
    return manifest


def build_report(
    path: str | Path = DEFAULT_MANIFEST,
    *,
    today: date | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(path)
    drills: list[GymDrill] = manifest["drills"]
    today = today or date.today()
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0)
    target_date = date.fromisoformat(str(manifest["target_demo_date"]))
    counts = Counter(drill.status for drill in drills)
    demo_critical = [drill for drill in drills if drill.demo_critical]
    critical_not_ready = [drill for drill in demo_critical if drill.status != "ready"]
    critical_blocked = [drill for drill in demo_critical if drill.status == "blocked"]
    next_attention = sorted(
        (drill for drill in drills if drill.status in ATTENTION_STATUSES),
        key=lambda drill: (drill.attention_rank, drill.due_date, drill.id),
    )
    readiness_status = "demo_ready" if not critical_not_ready else "training"
    if critical_blocked:
        readiness_status = "blocked"

    return {
        "schema_version": "foxclaw_gym_report.v0",
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "target_demo_date": target_date.isoformat(),
        "days_remaining": (target_date - today).days,
        "generated_for": manifest["generated_for"],
        "readiness_status": readiness_status,
        "authority": manifest["authority"],
        "counts": {status: counts.get(status, 0) for status in sorted(ALLOWED_STATUSES)},
        "demo_critical": {
            "total": len(demo_critical),
            "ready": sum(1 for drill in demo_critical if drill.status == "ready"),
            "not_ready": len(critical_not_ready),
            "blocked": len(critical_blocked),
        },
        "next_attention": [_drill_summary(drill) for drill in next_attention[:5]],
        "drills": [_drill_summary(drill) for drill in drills],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# FoxClaw Gym",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Target demo: `{report['target_demo_date']}` ({report['days_remaining']} days remaining)",
        f"Readiness: `{report['readiness_status']}`",
        "",
        "## Demo-Critical",
        "",
        f"- Ready: `{report['demo_critical']['ready']}` / `{report['demo_critical']['total']}`",
        f"- Not ready: `{report['demo_critical']['not_ready']}`",
        f"- Blocked: `{report['demo_critical']['blocked']}`",
        "",
        "## Next Attention",
        "",
    ]
    for item in report["next_attention"]:
        lines.append(
            f"- `{item['id']}` ({item['status']}, due {item['due_date']}): {item['next_action']}"
        )
    lines.extend(
        [
            "",
            "## Authority",
            "",
            "- `can_submit_order=false`",
            "- `can_move_funds=false`",
            "- `live_execution_allowed=false`",
            "",
        ]
    )
    return "\n".join(lines)


def _drill_summary(drill: GymDrill) -> dict[str, Any]:
    return {
        "id": drill.id,
        "name": drill.name,
        "lane": drill.lane,
        "status": drill.status,
        "demo_critical": drill.demo_critical,
        "due_date": drill.due_date,
        "purpose": drill.purpose,
        "proof_command": drill.proof_command,
        "demo_line": drill.demo_line,
        "next_action": drill.next_action,
    }


def _validate_authority(authority: dict[str, Any]) -> None:
    for key in ("can_submit_order", "can_move_funds", "live_execution_allowed"):
        if authority.get(key) is not False:
            raise ValueError(f"gym authority must keep {key}=false")
