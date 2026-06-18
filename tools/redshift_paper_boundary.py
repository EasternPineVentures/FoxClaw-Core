#!/usr/bin/env python3
"""Demonstrate the FoxClaw -> Redshift paper receipt boundary."""

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
from foxclaw.adapters.event_contracts.markets import to_jsonable  # noqa: E402
from foxclaw.adapters.redshift.paper_boundary import (  # noqa: E402
    export_foxclaw_decision,
    rehearse_redshift_paper_execution,
    settle_redshift_paper_execution,
    verify_execution_links_decision,
)


def fixture_forecast() -> ForecastReceipt:
    return ForecastReceipt(
        market_id="KXFOOTBALL-BOUNDARY-FIXTURE",
        side="yes",
        verdict="paper",
        independent_probability=Decimal("0.62"),
        market_probability=Decimal("0.43"),
        costs_total=Decimal("0.0200"),
        usable_edge=Decimal("0.1700"),
        minimum_usable_edge=Decimal("0.0500"),
        evidence_quality=Decimal("0.85"),
        dossier_hash="sha256:" + "a" * 64,
        engine_subject="forecast:event_contract:football",
        engine_tier="T2",
        gate_multiplier=Decimal("1.0000"),
        raw_commitment=Decimal("4.0000"),
        adjusted_commitment=Decimal("4.0000"),
        reason="Fixture proves Redshift can rehearse paper execution without authority.",
        code_version=_version(),
        created_at=datetime(2026, 6, 18, 0, 0, tzinfo=UTC),
    )


def build_fixture() -> dict:
    forecast = fixture_forecast()
    decision = export_foxclaw_decision(forecast)
    execution = rehearse_redshift_paper_execution(
        decision,
        requested_contracts=Decimal("4"),
        filled_contracts=Decimal("4"),
        fill_price=Decimal("0.45"),
        fees=Decimal("0.0000"),
        slippage=Decimal("0.0200"),
        executed_at=datetime(2026, 6, 18, 0, 1, tzinfo=UTC),
    )
    outcome = settle_redshift_paper_execution(
        execution,
        resolved_outcome="yes",
        settled_at=datetime(2026, 6, 19, 0, 0, tzinfo=UTC),
    )
    return {
        "boundary": "redshift_paper_boundary_v1",
        "mode": "PAPER",
        "linked": verify_execution_links_decision(decision, execution),
        "authority": {
            "foxclaw_can_submit_order": decision.can_submit_order,
            "redshift_can_submit_order": execution.can_submit_order,
            "can_move_funds": execution.can_move_funds,
            "live_execution_allowed": execution.live_execution_allowed,
            "redshift_capital_effect": execution.redshift_capital_effect,
            "can_mutate_foxclaw_decision": execution.can_mutate_foxclaw_decision,
        },
        "forecast": forecast,
        "decision_export": decision,
        "redshift_execution": execution,
        "redshift_outcome": outcome,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.fixture:
        raise SystemExit("Redshift Paper Boundary V1 currently requires --fixture")
    payload = build_fixture()
    if args.json:
        print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
    else:
        print(f"boundary: {payload['boundary']}")
        print(f"mode: {payload['mode']}")
        print(f"linked: {payload['linked']}")
        print(f"redshift_capital_effect: {payload['authority']['redshift_capital_effect']}")
        print(f"live_execution_allowed: {payload['authority']['live_execution_allowed']}")
    return 0


def _version() -> str:
    return (REPO / "VERSION").read_text(encoding="utf-8").strip()


if __name__ == "__main__":
    raise SystemExit(main())
