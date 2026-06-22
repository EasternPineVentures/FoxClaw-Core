from __future__ import annotations

import json
from pathlib import Path

import pytest

from foxclaw.nodes.lane_manifest import load_lane_manifest, resolve_node_lane


def test_lane_manifest_resolves_node_target(tmp_path: Path):
    manifest_path = tmp_path / "lanes.json"
    manifest_path.write_text(
        json.dumps(
            {
                "contract_version": "apollo_courier_lanes.v1",
                "default_remote": "origin",
                "lanes": {
                    "parser": {
                        "description": "parser lane",
                        "nodes": {
                            "A2": {
                                "target_branch": "feature/parser",
                                "role": "validate fixtures",
                                "repo_path_hint": "C:/node",
                                "notes": ["private corpus stays outside git"],
                            }
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = load_lane_manifest(manifest_path)
    target = resolve_node_lane(manifest, lane_id="parser", node_id="A2")

    assert manifest.default_remote == "origin"
    assert target.target_branch == "feature/parser"
    assert target.role == "validate fixtures"
    assert target.notes == ("private corpus stays outside git",)


def test_lane_manifest_rejects_unknown_lane_or_node(tmp_path: Path):
    manifest_path = tmp_path / "lanes.json"
    manifest_path.write_text(
        json.dumps(
            {
                "contract_version": "apollo_courier_lanes.v1",
                "default_remote": "origin",
                "lanes": {
                    "master": {
                        "nodes": {
                            "A1": {
                                "target_branch": "master",
                                "role": "integration",
                                "repo_path_hint": "C:/a1",
                            }
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = load_lane_manifest(manifest_path)
    with pytest.raises(ValueError, match="unknown Courier lane"):
        resolve_node_lane(manifest, lane_id="missing", node_id="A1")
    with pytest.raises(ValueError, match="has no node"):
        resolve_node_lane(manifest, lane_id="master", node_id="A2")
