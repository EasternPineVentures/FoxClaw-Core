#!/usr/bin/env python3
"""List local FoxClaw Ledger V0 review tasks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.ledger import DEFAULT_REVIEW_QUEUE_PATH  # noqa: E402
from foxclaw.ledger.review_queue import ReviewQueue  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--review-queue",
        default=str(DEFAULT_REVIEW_QUEUE_PATH),
        help="review-task JSONL path",
    )
    parser.add_argument("--status", help="filter review tasks by status")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args(argv)

    queue = ReviewQueue(args.review_queue)
    tasks = queue.list_tasks(status=args.status)
    payload = {
        "schema_version": "foxclaw_ledger_review_queue.v0",
        "review_queue": str(queue.path),
        "task_count": len(tasks),
        "tasks": tasks,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_markdown(payload))
    return 0


def _render_markdown(payload: dict) -> str:
    lines = [
        "# FoxClaw Ledger Review Queue",
        "",
        f"Queue: `{payload['review_queue']}`",
        f"Tasks shown: `{payload['task_count']}`",
        "",
    ]
    for task in payload["tasks"]:
        lines.append(
            f"- `{task['task_id']}` intent=`{task['linked_intent_id']}` "
            f"review_after=`{task['review_after']}` status=`{task['status']}`"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
