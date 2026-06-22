"""Apollo Courier lane manifest support."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Mapping

LANE_MANIFEST_VERSION = "apollo_courier_lanes.v1"


@dataclass(frozen=True)
class CourierNodeLane:
    node_id: str
    lane_id: str
    target_branch: str
    role: str
    repo_path_hint: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class CourierLane:
    lane_id: str
    description: str
    nodes: Mapping[str, CourierNodeLane]


@dataclass(frozen=True)
class CourierLaneManifest:
    contract_version: str
    default_remote: str
    lanes: Mapping[str, CourierLane]

    def __post_init__(self) -> None:
        if self.contract_version != LANE_MANIFEST_VERSION:
            raise ValueError(f"unsupported Courier lane manifest version: {self.contract_version}")
        if not self.default_remote.strip():
            raise ValueError("default_remote is required")
        if not self.lanes:
            raise ValueError("at least one Courier lane is required")


def load_lane_manifest(path: str | Path) -> CourierLaneManifest:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Courier lane manifest must be a JSON object")
    lanes_payload = payload.get("lanes")
    if not isinstance(lanes_payload, Mapping):
        raise ValueError("Courier lane manifest requires a lanes object")

    lanes: dict[str, CourierLane] = {}
    for lane_id, lane_payload in lanes_payload.items():
        if not isinstance(lane_payload, Mapping):
            raise ValueError(f"lane {lane_id} must be an object")
        nodes_payload = lane_payload.get("nodes")
        if not isinstance(nodes_payload, Mapping) or not nodes_payload:
            raise ValueError(f"lane {lane_id} requires a non-empty nodes object")
        nodes: dict[str, CourierNodeLane] = {}
        for node_id, node_payload in nodes_payload.items():
            if not isinstance(node_payload, Mapping):
                raise ValueError(f"lane {lane_id} node {node_id} must be an object")
            target_branch = _required_text(node_payload.get("target_branch"), f"{lane_id}.{node_id}.target_branch")
            role = _required_text(node_payload.get("role"), f"{lane_id}.{node_id}.role")
            repo_path_hint = _required_text(
                node_payload.get("repo_path_hint"),
                f"{lane_id}.{node_id}.repo_path_hint",
            )
            notes = tuple(str(item).strip() for item in node_payload.get("notes") or () if str(item).strip())
            nodes[str(node_id)] = CourierNodeLane(
                node_id=str(node_id),
                lane_id=str(lane_id),
                target_branch=target_branch,
                role=role,
                repo_path_hint=repo_path_hint,
                notes=notes,
            )
        lanes[str(lane_id)] = CourierLane(
            lane_id=str(lane_id),
            description=str(lane_payload.get("description") or "").strip(),
            nodes=nodes,
        )

    return CourierLaneManifest(
        contract_version=_required_text(payload.get("contract_version"), "contract_version"),
        default_remote=str(payload.get("default_remote") or "origin").strip(),
        lanes=lanes,
    )


def resolve_node_lane(
    manifest: CourierLaneManifest,
    *,
    lane_id: str,
    node_id: str,
) -> CourierNodeLane:
    try:
        lane = manifest.lanes[lane_id]
    except KeyError as exc:
        raise ValueError(f"unknown Courier lane: {lane_id}") from exc
    try:
        return lane.nodes[node_id]
    except KeyError as exc:
        available = ", ".join(sorted(lane.nodes)) or "none"
        raise ValueError(f"lane {lane_id} has no node {node_id}; available nodes: {available}") from exc


def lane_summary(manifest: CourierLaneManifest) -> dict[str, Any]:
    return {
        "contract_version": manifest.contract_version,
        "default_remote": manifest.default_remote,
        "lanes": {
            lane_id: {
                "description": lane.description,
                "nodes": {
                    node_id: {
                        "target_branch": node.target_branch,
                        "role": node.role,
                        "repo_path_hint": node.repo_path_hint,
                        "notes": list(node.notes),
                    }
                    for node_id, node in sorted(lane.nodes.items())
                },
            }
            for lane_id, lane in sorted(manifest.lanes.items())
        },
    }


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [to_jsonable(item) for item in value]
    return value


def _required_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text
