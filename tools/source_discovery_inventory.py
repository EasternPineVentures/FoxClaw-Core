#!/usr/bin/env python3
"""Report candidate information sources for FoxClaw-to-CoinFox packet intake."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.source_discovery import DEFAULT_INVENTORY, build_report, render_markdown  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    parser.add_argument("--limit", type=int, default=20, help="number of top sources to include")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="use deterministic date/time for tests and handoff examples",
    )
    args = parser.parse_args(argv)

    fixture_generated_at = datetime(2026, 6, 30, 15, 0, tzinfo=UTC) if args.fixture else None
    report = build_report(args.inventory, generated_at=fixture_generated_at, limit=args.limit)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
