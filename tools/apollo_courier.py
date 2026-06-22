#!/usr/bin/env python3
"""Apollo Courier operator CLI.

Courier wraps two related founder-node jobs:

- safe branch positioning for A1/A2 workstations;
- signed Apollo Mesh messages for node-to-node coordination.
"""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.nodes.branch_sync import (  # noqa: E402
    apply_branch_sync,
    dumps_json,
    fetch_remote,
    inspect_branch_sync,
    plan_branch_sync,
    to_jsonable,
)
from foxclaw.nodes.lane_manifest import (  # noqa: E402
    lane_summary,
    load_lane_manifest,
    resolve_node_lane,
)

DEFAULT_LANE_MANIFEST = REPO / "config" / "apollo_courier_lanes.json"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "branch-sync":
        return _branch_sync(args[1:])
    if args and args[0] == "lanes":
        return _lanes(args[1:])
    if args and args[0] == "lane-sync":
        return _lane_sync(args[1:])
    _run_mesh(args)
    return 0


def _branch_sync(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect or safely align this repo to an expected branch.",
    )
    parser.add_argument("--repo", default=str(REPO))
    parser.add_argument("--target-branch", required=True)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--fetch", action="store_true", help="refresh remote refs before planning")
    parser.add_argument("--apply", action="store_true", help="perform the safe switch/pull plan")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.apply:
        result = apply_branch_sync(
            args.repo,
            target_branch=args.target_branch,
            remote=args.remote,
            fetch=True,
        )
        return _emit(to_jsonable(result), json_mode=args.json)

    if args.fetch:
        fetch_remote(args.repo, remote=args.remote)
    state = inspect_branch_sync(args.repo, target_branch=args.target_branch, remote=args.remote)
    plan = plan_branch_sync(state)
    return _emit({"state": state, "plan": plan, "applied": False}, json_mode=args.json)


def _lanes(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="List configured Apollo Courier lanes.")
    parser.add_argument("--manifest", default=str(DEFAULT_LANE_MANIFEST))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    manifest = load_lane_manifest(args.manifest)
    payload = lane_summary(manifest)
    if args.json:
        print(dumps_json(payload), end="")
        return 0
    print(f"manifest: {args.manifest}")
    print(f"contract_version: {payload['contract_version']}")
    print(f"default_remote: {payload['default_remote']}")
    for lane_id, lane in payload["lanes"].items():
        print(f"\n[{lane_id}] {lane['description']}")
        for node_id, node in lane["nodes"].items():
            print(f"- {node_id}: {node['target_branch']} ({node['role']})")
    return 0


def _lane_sync(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve a node lane and inspect or safely align the repo to its target branch.",
    )
    parser.add_argument("--repo", default=str(REPO))
    parser.add_argument("--manifest", default=str(DEFAULT_LANE_MANIFEST))
    parser.add_argument("--lane", required=True)
    parser.add_argument("--node-id", required=True)
    parser.add_argument("--remote")
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    manifest = load_lane_manifest(args.manifest)
    node_lane = resolve_node_lane(manifest, lane_id=args.lane, node_id=args.node_id)
    remote = args.remote or manifest.default_remote
    if args.apply:
        result = apply_branch_sync(
            args.repo,
            target_branch=node_lane.target_branch,
            remote=remote,
            fetch=True,
        )
        payload = {
            "lane": node_lane,
            "remote": remote,
            "applied": result.applied,
            "before": result.before,
            "plan": result.plan,
            "after": result.after,
            "executed": result.executed,
        }
        return _emit(payload, json_mode=args.json)

    if args.fetch:
        fetch_remote(args.repo, remote=remote)
    state = inspect_branch_sync(args.repo, target_branch=node_lane.target_branch, remote=remote)
    plan = plan_branch_sync(state)
    return _emit(
        {
            "lane": node_lane,
            "remote": remote,
            "state": state,
            "plan": plan,
            "applied": False,
        },
        json_mode=args.json,
    )


def _emit(payload: object, *, json_mode: bool) -> int:
    if json_mode:
        print(dumps_json(payload), end="")
        return 0
    data = to_jsonable(payload)
    plan = data.get("plan", {}) if isinstance(data, dict) else {}
    state = data.get("state") or data.get("before") or {}
    lane = data.get("lane") or {}
    if lane:
        print(f"lane: {lane.get('lane_id')}")
        print(f"node_id: {lane.get('node_id')}")
        print(f"role: {lane.get('role')}")
    print(f"repo: {state.get('repo_path')}")
    print(f"current_branch: {state.get('current_branch')}")
    print(f"target_branch: {state.get('target_branch')}")
    print(f"head: {state.get('head')} - {state.get('head_subject')}")
    print(f"upstream: {state.get('upstream') or 'none'}")
    print(f"ahead/behind: {state.get('ahead')}/{state.get('behind')}")
    print(f"dirty: {state.get('dirty')}")
    print(f"action: {plan.get('action')}")
    print(f"safe_to_apply: {plan.get('safe_to_apply')}")
    if data.get("applied"):
        after = data.get("after") or {}
        print(f"after_branch: {after.get('current_branch')}")
        print(f"after_ahead/behind: {after.get('ahead')}/{after.get('behind')}")
    notes = plan.get("notes") or ()
    if notes:
        print("notes:")
        for note in notes:
            print(f"- {note}")
    return 0


def _run_mesh(argv: list[str]) -> None:
    sys.argv = [str(Path(__file__).with_name("apollo_mesh.py")), *argv]
    runpy.run_path(str(Path(__file__).with_name("apollo_mesh.py")), run_name="__main__")


if __name__ == "__main__":
    raise SystemExit(main())
