#!/usr/bin/env python3
"""Build a Forecast Desk scoreboard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.event_contracts.scoring import build_forecast_scoreboard  # noqa: E402


def fixture_rows():
    return [
        {
            "category": "economics",
            "forecast_probability": "0.62",
            "market_probability": "0.43",
            "outcome_yes": True,
            "net_result": "3.99",
        },
        {
            "category": "economics",
            "forecast_probability": "0.30",
            "market_probability": "0.45",
            "outcome_yes": False,
            "net_result": "1.25",
        },
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--write")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.fixture:
        raise SystemExit("Phase F scoreboard CLI currently requires --fixture")
    report = build_forecast_scoreboard(fixture_rows())
    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json or not args.write:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
