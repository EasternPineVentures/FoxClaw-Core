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


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "branch-sync":
        return _branch_sync(args[1:])
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


def _emit(payload: object, *, json_mode: bool) -> int:
    if json_mode:
        print(dumps_json(payload), end="")
        return 0
    data = to_jsonable(payload)
    plan = data.get("plan", {}) if isinstance(data, dict) else {}
    state = data.get("state") or data.get("before") or {}
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
