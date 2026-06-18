#!/usr/bin/env python3
"""Evaluate the Forecast Desk self-funding claim gate."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.event_contracts.markets import to_jsonable  # noqa: E402
from foxclaw.adapters.event_contracts.self_funding import evaluate_self_funding  # noqa: E402

STANDARD = REPO / "config" / "self_funding_standard.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--write")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.fixture:
        raise SystemExit("Phase F self-funding CLI currently requires --fixture")
    standard = json.loads(STANDARD.read_text(encoding="utf-8"))
    report = evaluate_self_funding(
        mode="paper",
        resolved_positions=12,
        consecutive_days=7,
        net_economic_profit=Decimal("42.00"),
        operating_costs=Decimal("120.00"),
        standard=standard,
    )
    payload = to_jsonable(report)
    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json or not args.write:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
