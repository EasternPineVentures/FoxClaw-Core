#!/usr/bin/env python3
"""Forecast Desk health and silence diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

SILENCE_REASONS = (
    "no_open_markets",
    "stale_snapshot",
    "insufficient_liquidity",
    "resolution_ambiguous",
    "insufficient_evidence",
    "no_positive_usable_edge",
    "correlation_cap",
    "paper_capital_full",
    "venue_unavailable",
    "api_rate_limited",
)


def build_status(*, fixture: bool = False) -> dict:
    return {
        "mode": "PAPER",
        "status": "ok",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "fixture_mode": fixture,
        "can_submit_order": False,
        "can_move_funds": False,
        "live_execution_allowed": False,
        "silence_reasons": list(SILENCE_REASONS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    status = build_status(fixture=args.fixture)
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        for key, value in status.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
