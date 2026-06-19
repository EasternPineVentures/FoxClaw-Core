#!/usr/bin/env python3
"""Build Forecast Desk learning receipts from resolved paper outcomes."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.event_contracts.contracts import ForecastReceipt  # noqa: E402
from foxclaw.adapters.event_contracts.learning import build_learning_receipt  # noqa: E402
from foxclaw.adapters.event_contracts.markets import to_jsonable  # noqa: E402
from foxclaw.adapters.event_contracts.paper import PaperOutcome  # noqa: E402
from foxclaw.adapters.event_contracts.storage.repositories import ForecastRepository  # noqa: E402


def fixture_learning_receipt():
    forecast = ForecastReceipt(
        market_id="KXJOBLESS-26JUN18-T250",
        side="yes",
        verdict="paper",
        independent_probability=Decimal("0.62"),
        market_probability=Decimal("0.43"),
        costs_total=Decimal("0.0000"),
        usable_edge=Decimal("0.1900"),
        minimum_usable_edge=Decimal("0.0500"),
        evidence_quality=Decimal("0.82"),
        dossier_hash="sha256:" + "a" * 64,
        engine_subject="forecast:KXJOBLESS-26JUN18-T250:yes",
        engine_tier="allow",
        gate_multiplier=Decimal("1"),
        raw_commitment=Decimal("0.1900"),
        adjusted_commitment=Decimal("0.1900"),
        reason="paper_candidate",
        code_version="fixture",
        created_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
    )
    outcome = PaperOutcome(
        position_id="paper:KXJOBLESS-26JUN18-T250:yes:fixture",
        market_id=forecast.market_id,
        side="yes",
        resolved_outcome="yes",
        payout=Decimal("7.0000"),
        entry_cost=Decimal("3.0100"),
        fees=Decimal("0.0000"),
        net_result=Decimal("3.9900"),
        settled_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
    )
    return build_learning_receipt(
        forecast=forecast,
        outcome=outcome,
        created_at=datetime(2026, 6, 18, 13, 5, tzinfo=UTC),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--db")
    parser.add_argument("--write")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.fixture:
        raise SystemExit("Learning Spine V1 currently requires --fixture")

    receipt = fixture_learning_receipt()
    recorded = False
    if args.db:
        repo = ForecastRepository(args.db)
        repo.init_db()
        repo.record_learning_receipt(receipt)
        recorded = True

    payload = {
        "learning_receipt": to_jsonable(receipt),
        "recorded": recorded,
        "authority": {
            "can_set_probability": False,
            "can_submit_order": False,
            "can_move_funds": False,
            "live_execution_allowed": False,
        },
    }
    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json or not args.write:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
