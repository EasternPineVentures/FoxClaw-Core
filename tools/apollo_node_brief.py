#!/usr/bin/env python3
"""Generate a pasteable FoxClaw Apollo node coordination brief."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.nodes.apollo import (  # noqa: E402
    GitSnapshot,
    build_node_brief,
    dumps_json,
    render_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(REPO), help="repo root to inspect")
    parser.add_argument("--node-id", help="this node id, for example A1 or A2")
    parser.add_argument("--peer-node", default="peer", help="target node id")
    parser.add_argument("--role", default="operator")
    parser.add_argument("--current-slice", default="status handoff")
    parser.add_argument(
        "--next-request",
        default="pull, inspect status, and continue the smallest safe slice",
    )
    parser.add_argument("--blocker", action="append", default=[])
    parser.add_argument("--note", action="append", default=[])
    parser.add_argument("--old-reference-path")
    parser.add_argument("--write", help="optional output path")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="use deterministic git metadata for tests and examples",
    )
    args = parser.parse_args(argv)

    git = _fixture_git(args.repo) if args.fixture else None
    generated_at = datetime(2026, 6, 18, 0, 0, tzinfo=UTC) if args.fixture else None
    brief = build_node_brief(
        repo_path=args.repo,
        node_id=args.node_id,
        peer_node=args.peer_node,
        role=args.role,
        current_slice=args.current_slice,
        next_request=args.next_request,
        blockers=tuple(args.blocker),
        notes=tuple(args.note),
        old_reference_path=args.old_reference_path,
        generated_at=generated_at,
        git=git,
    )
    output = dumps_json(brief) if args.json else render_markdown(brief)
    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


def _fixture_git(repo: str) -> GitSnapshot:
    return GitSnapshot(
        repo_path=str(Path(repo).resolve()),
        branch="master",
        head="fixture",
        head_subject="Fixture Apollo node brief",
        upstream="origin/master",
        ahead=0,
        behind=0,
        dirty=False,
        changed_files=(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
