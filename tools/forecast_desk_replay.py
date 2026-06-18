#!/usr/bin/env python3
"""Replay paper Forecast Desk positions without future leakage."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.event_contracts.markets import to_jsonable  # noqa: E402
from foxclaw.adapters.event_contracts.paper import PaperPosition, replay_positions  # noqa: E402
from foxclaw.adapters.event_contracts.resolution import record_resolution  # noqa: E402


def fixture_manifest() -> dict:
    opened_at = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    position = PaperPosition(
        position_id="paper:fixture",
        market_id="KXJOBLESS-26JUN18-T250",
        side="yes",
        requested_contracts=__import__("decimal").Decimal("10.00"),
        filled_contracts=__import__("decimal").Decimal("7.00"),
        fill_status="partial",
        entry_price=__import__("decimal").Decimal("0.4300"),
        entry_cost=__import__("decimal").Decimal("3.0100"),
        fee_paid=__import__("decimal").Decimal("0.0000"),
        fee_model_version="kalshi_fee_model_v0_explicit_zero",
        opened_at=opened_at,
        source_receipt_hash="sha256:fixture",
    )
    resolution = record_resolution(
        {"market_id": position.market_id},
        "yes",
        "https://example.invalid/result",
        resolved_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
    )
    return replay_positions([position], {position.market_id: resolution})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true", help="write a deterministic fixture replay")
    parser.add_argument("--write")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.fixture:
        raise SystemExit("Phase E replay CLI currently requires --fixture")
    manifest = fixture_manifest()
    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(to_jsonable(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json or not args.write:
        print(json.dumps(to_jsonable(manifest), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
