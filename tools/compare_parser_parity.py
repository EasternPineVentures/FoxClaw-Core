#!/usr/bin/env python3
"""Compare offline v13 parser-compat output with sanitized expected v1 records."""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any, Mapping

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.market.signals.legacy_v13 import PARSER_VERSION, parse_raw_source_event  # noqa: E402
from foxclaw.adapters.market.signals.normalization import canonical_decimal  # noqa: E402

DEFAULT_FIXTURE_DIR = REPO / "tests" / "fixtures" / "parser_v1"

FIELDS = (
    "accepted",
    "reason_code",
    "candidate_type",
    "symbol",
    "side",
    "entry_price",
    "quantity",
    "stop_loss",
    "take_profit",
    "duplicate_disposition",
)
NUMERIC_FIELDS = {"entry_price", "quantity", "stop_loss", "take_profit"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-dir", default=str(DEFAULT_FIXTURE_DIR))
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    report = compare_fixture_dir(Path(args.fixtures_dir))
    if args.json:
        print(json.dumps(report, sort_keys=True, separators=(",", ":"), default=str))
    else:
        print(
            f"fixtures={report['fixture_count']} matched={report['matched']} "
            f"mismatches={report['mismatch_count']}"
        )
        for mismatch in report["mismatches"]:
            print(f"{mismatch['fixture_id']}: {mismatch['field']} {mismatch['mismatch_class']}")
    return 0 if report["mismatch_count"] == 0 else 1


def compare_fixture_dir(path: Path) -> dict[str, Any]:
    fixtures = sorted(item for item in path.resolve().glob("*.json") if item.is_file())
    seen_dedupes: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []

    for fixture_path in fixtures:
        envelope = _load(fixture_path)
        fixture_id = str(envelope.get("fixture_id") or fixture_path.stem)
        result = parse_raw_source_event(envelope, mode="fixture")
        duplicate_disposition = _duplicate_disposition(
            result.dedupe_key,
            fixture_id=fixture_id,
            seen=seen_dedupes,
        )
        actual = _actual_record(result, duplicate_disposition=duplicate_disposition)
        expected = envelope.get("expected_v1")
        if not isinstance(expected, Mapping):
            expected = {}
        fixture_mismatches = _compare_record(
            fixture_id=fixture_id,
            expected=expected,
            actual=actual,
        )
        records.append(
            {
                "fixture_id": fixture_id,
                "parser_version": PARSER_VERSION,
                "accepted": actual["accepted"],
                "reason_code": actual["reason_code"],
                "duplicate_disposition": duplicate_disposition,
                "mismatch_class": "MATCH" if not fixture_mismatches else "PARSER_BEHAVIOR_REGRESSION",
            }
        )
        mismatches.extend(fixture_mismatches)

    return {
        "schema_version": "parser_parity_report.v0",
        "parser_version": PARSER_VERSION,
        "fixture_count": len(fixtures),
        "matched": len(fixtures) - len({m["fixture_id"] for m in mismatches}),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "records": records,
        "standard": {
            "accepted_status": "exact",
            "rejection_reason": "exact",
            "candidate_type": "exact",
            "symbol": "exact_normalized",
            "side": "exact",
            "numeric": "canonical_decimal",
            "safety_relevant_unexplained_mismatches": 0,
        },
        "writes": [],
        "network": False,
        "coinfox": False,
        "execution_authority": False,
    }


def _actual_record(result: Any, *, duplicate_disposition: str) -> dict[str, Any]:
    payload = result.normalized_payload
    return {
        "accepted": result.accepted,
        "reason_code": result.reason_code,
        "candidate_type": payload.get("candidate_type"),
        "symbol": payload.get("symbol"),
        "side": payload.get("side"),
        "entry_price": payload.get("entry_price"),
        "quantity": payload.get("quantity"),
        "stop_loss": payload.get("stop_loss"),
        "take_profit": payload.get("take_profit"),
        "duplicate_disposition": duplicate_disposition,
    }


def _compare_record(
    *,
    fixture_id: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    for field in FIELDS:
        if field not in expected:
            continue
        expected_value = expected.get(field)
        actual_value = actual.get(field)
        if field in NUMERIC_FIELDS:
            if _canonical_number(expected_value) == _canonical_number(actual_value):
                continue
        elif expected_value == actual_value:
            continue
        mismatches.append(
            {
                "fixture_id": fixture_id,
                "field": field,
                "mismatch_class": "PARSER_BEHAVIOR_REGRESSION",
                "expected_path": f"$.expected_v1.{field}",
                "actual_path": f"$.records[{fixture_id!r}].{field}",
            }
        )
    return mismatches


def _duplicate_disposition(dedupe_key: str, *, fixture_id: str, seen: dict[str, str]) -> str:
    first = seen.get(dedupe_key)
    if first is None:
        seen[dedupe_key] = fixture_id
        return "accepted_once"
    return "rejected_duplicate"


def _canonical_number(value: Any) -> str | None:
    normalized = canonical_decimal(value)
    if normalized is None:
        return None
    try:
        return str(Decimal(normalized))
    except (InvalidOperation, ValueError):
        return normalized


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"fixture must be a JSON object: {path}")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
