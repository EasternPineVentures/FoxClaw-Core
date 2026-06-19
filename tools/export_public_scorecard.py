#!/usr/bin/env python3
"""Build the public scorecard export from public intelligence fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.contract.public.export import build_scorecard_export, load_fixture_cards  # noqa: E402

DEFAULT_FIXTURE_DIR = REPO / "tests" / "fixtures" / "public_contract"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true", help="use checked-in fixture cards")
    parser.add_argument("--fixture-dir", default=str(DEFAULT_FIXTURE_DIR), help="fixture directory")
    parser.add_argument("--output", help="optional scorecard JSON path")
    args = parser.parse_args(argv)

    if not args.fixture:
        parser.error("only --fixture scorecard export is implemented until live parser parity lands")

    scorecard = build_scorecard_export(load_fixture_cards(args.fixture_dir))
    text = json.dumps(scorecard, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
