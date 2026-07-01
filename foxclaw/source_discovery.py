"""Source discovery inventory reporting for CoinFox packet intake."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_INVENTORY = Path(__file__).resolve().parent.parent / "config" / "source_discovery_inventory.json"
ALLOWED_STATUSES = {
    "manual_now",
    "adapter_later",
    "adapter_later_terms_review",
    "deferred_terms_review",
    "deferred_private_policy",
}
ALLOWED_TRUST_STATES = {"trusted", "watch", "quarantined", "deferred"}
AUTHORITY_KEYS = (
    "can_submit_order",
    "can_move_funds",
    "live_execution_allowed",
    "can_publish_to_coinfox",
    "can_change_source_reliability",
    "can_update_verified_memory",
    "can_train_model",
)


@dataclass(frozen=True)
class DiscoverySource:
    id: str
    display_name: str
    category: str
    source_type: str
    priority: int
    speed: str
    access_mode: str
    automation_status: str
    trust_state: str
    public_safe_default: bool
    requires_corroboration_count: int
    why_it_matters: str
    what_to_capture: str
    safety_notes: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DiscoverySource":
        missing = {
            "id",
            "display_name",
            "category",
            "source_type",
            "priority",
            "speed",
            "access_mode",
            "automation_status",
            "trust_state",
            "public_safe_default",
            "requires_corroboration_count",
            "why_it_matters",
            "what_to_capture",
            "safety_notes",
        } - set(payload)
        if missing:
            raise ValueError(f"discovery source missing required fields: {sorted(missing)}")
        status = str(payload["automation_status"])
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"unknown source automation_status: {status}")
        trust_state = str(payload["trust_state"])
        if trust_state not in ALLOWED_TRUST_STATES:
            raise ValueError(f"unknown source trust_state: {trust_state}")
        priority = int(payload["priority"])
        if priority < 1 or priority > 5:
            raise ValueError(f"source priority must be 1-5: {payload['id']}")
        corroborations = int(payload["requires_corroboration_count"])
        if corroborations < 0:
            raise ValueError(f"corroboration count cannot be negative: {payload['id']}")
        return cls(
            id=str(payload["id"]),
            display_name=str(payload["display_name"]),
            category=str(payload["category"]),
            source_type=str(payload["source_type"]),
            priority=priority,
            speed=str(payload["speed"]),
            access_mode=str(payload["access_mode"]),
            automation_status=status,
            trust_state=trust_state,
            public_safe_default=bool(payload["public_safe_default"]),
            requires_corroboration_count=corroborations,
            why_it_matters=str(payload["why_it_matters"]),
            what_to_capture=str(payload["what_to_capture"]),
            safety_notes=str(payload["safety_notes"]),
        )


def load_inventory(path: str | Path = DEFAULT_INVENTORY) -> dict[str, Any]:
    inventory = json.loads(Path(path).read_text(encoding="utf-8"))
    if inventory.get("schema_version") != "source_discovery_inventory.v0":
        raise ValueError("source discovery inventory must use schema_version source_discovery_inventory.v0")
    _validate_authority(inventory.get("authority", {}))
    sources = [DiscoverySource.from_dict(item) for item in inventory.get("sources", [])]
    if not sources:
        raise ValueError("source discovery inventory must contain at least one source")
    source_ids = [source.id for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source discovery inventory has duplicate source IDs")
    inventory["sources"] = sources
    return inventory


def build_report(
    path: str | Path = DEFAULT_INVENTORY,
    *,
    generated_at: datetime | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    inventory = load_inventory(path)
    sources: list[DiscoverySource] = inventory["sources"]
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0)
    categories = Counter(source.category for source in sources)
    statuses = Counter(source.automation_status for source in sources)
    trust_states = Counter(source.trust_state for source in sources)
    fast_manual = [
        source
        for source in sources
        if source.automation_status == "manual_now" and source.speed == "fast"
    ]
    reddit_sources = [source for source in sources if source.category == "reddit"]
    social_sources = [
        source
        for source in sources
        if source.category in {"reddit", "social_market", "social_video", "social_chat"}
    ]
    top_sources = sorted(
        sources,
        key=lambda source: (
            source.priority,
            _speed_rank(source.speed),
            source.category,
            source.id,
        ),
    )[:limit]

    return {
        "schema_version": "source_discovery_report.v0",
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "generated_for": inventory["generated_for"],
        "authority": inventory["authority"],
        "source_count": len(sources),
        "category_counts": dict(sorted(categories.items())),
        "automation_status_counts": dict(sorted(statuses.items())),
        "trust_state_counts": dict(sorted(trust_states.items())),
        "reddit_source_count": len(reddit_sources),
        "social_source_count": len(social_sources),
        "fast_manual_count": len(fast_manual),
        "top_sources": [_source_summary(source) for source in top_sources],
        "reddit_sources": [_source_summary(source) for source in reddit_sources],
        "fast_manual_sources": [_source_summary(source) for source in fast_manual],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Source Discovery Inventory",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Sources: `{report['source_count']}`",
        f"Reddit sources: `{report['reddit_source_count']}`",
        f"Fast manual sources: `{report['fast_manual_count']}`",
        "",
        "## Fast First",
        "",
    ]
    for item in report["top_sources"][:15]:
        lines.append(
            f"- `{item['id']}` ({item['category']}, {item['trust_state']}): "
            f"{item['why_it_matters']}"
        )
    lines.extend(["", "## Reddit Watchlist", ""])
    for item in report["reddit_sources"]:
        lines.append(
            f"- `{item['display_name']}`: {item['what_to_capture']}"
        )
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
            "- `can_train_model=false`",
            "",
        ]
    )
    return "\n".join(lines)


def _source_summary(source: DiscoverySource) -> dict[str, Any]:
    return {
        "id": source.id,
        "display_name": source.display_name,
        "category": source.category,
        "source_type": source.source_type,
        "priority": source.priority,
        "speed": source.speed,
        "access_mode": source.access_mode,
        "automation_status": source.automation_status,
        "trust_state": source.trust_state,
        "public_safe_default": source.public_safe_default,
        "requires_corroboration_count": source.requires_corroboration_count,
        "why_it_matters": source.why_it_matters,
        "what_to_capture": source.what_to_capture,
        "safety_notes": source.safety_notes,
    }


def _speed_rank(speed: str) -> int:
    return {"fast": 0, "medium": 1, "slow": 2}.get(speed, 3)


def _validate_authority(authority: dict[str, Any]) -> None:
    for key in AUTHORITY_KEYS:
        if authority.get(key) is not False:
            raise ValueError(f"source discovery authority must keep {key}=false")
