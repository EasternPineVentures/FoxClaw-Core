"""Public source registry defaults for intake quarantine decisions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .quarantine import default_source_state

REPO = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = REPO / "config" / "public_source_registry.json"
VALID_TRUST_STATES = {"trusted", "quarantined", "watch"}
REQUIRED_SOURCE_FIELDS = ("source_id", "display_name", "source_type", "trust_state")


def load_source_registry(path: str | None = None) -> dict[str, Any]:
    """Load and validate the public source registry JSON."""
    registry_path = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    if not registry_path.exists():
        raise FileNotFoundError(f"source registry not found: {registry_path}")
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid source registry JSON at {registry_path}: {exc}") from exc
    if not isinstance(registry, dict):
        raise ValueError(f"source registry must be a JSON object: {registry_path}")
    validation = validate_source_registry(registry)
    if not validation["valid"]:
        errors = "; ".join(str(error) for error in validation["errors"])
        raise ValueError(f"invalid source registry at {registry_path}: {errors}")
    return registry


def get_source_policy(source_id: str, registry: dict[str, Any] | None = None) -> dict[str, object]:
    """Return a source-state-compatible policy for a known or unknown source."""
    normalized_id = str(source_id or "unknown_source").strip() or "unknown_source"
    active_registry = registry if registry is not None else load_source_registry()
    for entry in active_registry.get("sources", []):
        if str(entry.get("source_id", "")).strip() == normalized_id:
            return _normalize_registry_entry(entry)

    state = default_source_state(normalized_id)
    state.update(
        {
            "requires_prompt_injection_scan": True,
            "requires_corroboration_count": int(
                active_registry.get("default_policy", {}).get(
                    "social_sources_require_corroboration_count", 2
                )
            ),
            "public_safe": False,
        }
    )
    return state


def list_sources_by_trust_state(
    trust_state: str,
    registry: dict[str, Any] | None = None,
) -> list[dict[str, object]]:
    """List normalized source policies by trust state."""
    requested = str(trust_state or "").strip().lower()
    active_registry = registry if registry is not None else load_source_registry()
    return [
        _normalize_registry_entry(entry)
        for entry in active_registry.get("sources", [])
        if str(entry.get("trust_state", "")).strip().lower() == requested
    ]


def validate_source_registry(registry: dict[str, Any]) -> dict[str, object]:
    """Validate Source Registry V0 without mutating it."""
    errors: list[str] = []
    if not isinstance(registry, dict):
        return {"valid": False, "errors": ["registry must be a dict"], "source_count": 0}
    if not registry.get("registry_version"):
        errors.append("registry_version is required")

    sources = registry.get("sources")
    if not isinstance(sources, list):
        return {
            "valid": False,
            "errors": [*errors, "sources must be a list"],
            "source_count": 0,
        }

    seen: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"sources[{index}] must be an object")
            continue
        source_id = str(source.get("source_id", "")).strip()
        for field in REQUIRED_SOURCE_FIELDS:
            if not source.get(field):
                errors.append(f"{source_id or f'sources[{index}]'} missing {field}")
        if source_id:
            if source_id in seen:
                errors.append(f"duplicate source_id: {source_id}")
            seen.add(source_id)
        trust_state = str(source.get("trust_state", "")).strip().lower()
        if trust_state and trust_state not in VALID_TRUST_STATES:
            errors.append(f"{source_id or f'sources[{index}]'} invalid trust_state: {trust_state}")
        if source.get("can_train_model") is not False:
            errors.append(f"{source_id or f'sources[{index}]'} can_train_model must be false")
        if source.get("can_update_verified_memory") is not False:
            errors.append(
                f"{source_id or f'sources[{index}]'} can_update_verified_memory must be false"
            )
        if trust_state == "trusted" and source.get("requires_prompt_injection_scan") is not True:
            errors.append(
                f"{source_id or f'sources[{index}]'} trusted source must require prompt scan"
            )

    return {"valid": not errors, "errors": errors, "source_count": len(sources)}


def _normalize_registry_entry(entry: dict[str, Any]) -> dict[str, object]:
    return {
        "source_id": str(entry["source_id"]),
        "source_type": str(entry["source_type"]),
        "trust_state": str(entry["trust_state"]).strip().lower(),
        "can_influence_public_packet": bool(entry.get("can_influence_public_packet", False)),
        "can_train_model": False,
        "can_update_verified_memory": False,
        "observation_count": 0,
        "requires_prompt_injection_scan": bool(entry.get("requires_prompt_injection_scan", True)),
        "requires_corroboration_count": int(entry.get("requires_corroboration_count", 0)),
        "public_safe": bool(entry.get("public_safe", False)),
    }
