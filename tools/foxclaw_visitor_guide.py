#!/usr/bin/env python3
"""Print the plain-language FoxClaw first-encounter guide."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.visitor import build_visitor_guide, render_visitor_guide_markdown  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    parser.add_argument("--fixture", action="store_true", help="use deterministic timestamp")
    args = parser.parse_args(argv)

    generated_at = datetime(2026, 6, 19, 18, 0, tzinfo=UTC) if args.fixture else None
    guide = build_visitor_guide(generated_at=generated_at)
    if args.json:
        print(json.dumps(guide, indent=2, sort_keys=True))
    else:
        print(render_visitor_guide_markdown(guide))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
