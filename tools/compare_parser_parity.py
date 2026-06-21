#!/usr/bin/env python3
"""Compare offline v13 parser-compat output with legacy v1 parser results."""
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
from foxclaw.contract.internal import schema_path  # noqa: E402
from foxclaw.contract.public.schema_validation import validate_json_schema  # noqa: E402
from tools.validate_parser_legacy_results import load_valid_legacy_results  # noqa: E402

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
    "parser_confidence",
    "duplicate_disposition",
)
NUMERIC_FIELDS = {"entry_price", "quantity", "stop_loss", "take_profit"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-dir", default=str(DEFAULT_FIXTURE_DIR))
    parser.add_argument(
        "--legacy-jsonl",
        help="schema-valid parser_legacy_result.v1 JSONL produced by A2",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    try:
        report = compare_fixture_dir(
            Path(args.fixtures_dir),
            legacy_jsonl=Path(args.legacy_jsonl) if args.legacy_jsonl else None,
        )
    except ValueError as exc:
        print(f"parser parity error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, sort_keys=True, separators=(",", ":"), default=str))
    else:
        print(
            f"fixtures={report['fixture_count']} matched={report['matched']} "
            f"mismatches={report['mismatch_count']}"
        )
        for mismatch in report["mismatches"]:
            print(f"{mismatch['case_id']}: {mismatch['field']} {mismatch['mismatch_class']}")
    return 0 if report["mismatch_count"] == 0 else 1


def compare_fixture_dir(path: Path, *, legacy_jsonl: Path | None = None) -> dict[str, Any]:
    fixtures = sorted(item for item in path.resolve().glob("*.json") if item.is_file())
    seen_dedupes: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    legacy_by_case = _legacy_by_case(legacy_jsonl) if legacy_jsonl else {}
    fixture_case_ids: set[str] = set()

    for fixture_path in fixtures:
        envelope = _load(fixture_path)
        fixture_id = str(envelope.get("fixture_id") or fixture_path.stem)
        case_id = str(envelope.get("case_id") or fixture_id)
        fixture_case_ids.add(case_id)
        result = parse_raw_source_event(envelope, mode="fixture")
        duplicate_disposition = _duplicate_disposition(
            result.dedupe_key,
            case_id=case_id,
            seen=seen_dedupes,
        )
        actual = _actual_record(result, duplicate_disposition=duplicate_disposition)
        if legacy_by_case:
            expected = legacy_by_case.get(case_id)
            if expected is None:
                fixture_mismatches = [
                    _mismatch(case_id, "case_id", "$.legacy_jsonl", "$.fixtures", "UNKNOWN_REVIEW")
                ]
                expected_record: Mapping[str, Any] = {}
            else:
                expected_record = _expected_from_legacy(expected)
                fixture_mismatches = _compare_record(
                    case_id=case_id,
                    expected=expected_record,
                    actual=actual,
                )
        else:
            expected_record = envelope.get("expected_v1")
            if not isinstance(expected_record, Mapping):
                expected_record = {}
            fixture_mismatches = _compare_record(
                case_id=case_id,
                expected=expected_record,
                actual=actual,
            )
        records.append(
            {
                "case_id": case_id,
                "fixture_id": fixture_id,
                "parser_version": PARSER_VERSION,
                "accepted": actual["accepted"],
                "reason_code": actual["reason_code"],
                "duplicate_disposition": duplicate_disposition,
                "mismatch_class": "MATCH" if not fixture_mismatches else "PARSER_BEHAVIOR_REGRESSION",
            }
        )
        mismatches.extend(fixture_mismatches)

    for case_id in sorted(set(legacy_by_case) - fixture_case_ids):
        mismatches.append(
            _mismatch(case_id, "case_id", "$.legacy_jsonl", "$.fixtures", "UNKNOWN_REVIEW")
        )

    matched_cases = {record["case_id"] for record in records} - {m["case_id"] for m in mismatches}
    report = {
        "schema_version": "parser_parity_report.v1",
        "parser_version": PARSER_VERSION,
        "fixture_count": len(fixtures),
        "legacy_result_count": len(legacy_by_case),
        "matched": len(matched_cases),
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
    validate_json_schema(report, _schema("parser_parity_report.schema.json"))
    return report


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
        "parser_confidence": result.parser_confidence,
        "duplicate_disposition": duplicate_disposition,
    }


def _compare_record(
    *,
    case_id: str,
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
        mismatches.append(_mismatch(case_id, field, f"$.expected.{field}", f"$.actual.{field}"))
    return mismatches


def _duplicate_disposition(dedupe_key: str, *, case_id: str, seen: dict[str, str]) -> str:
    first = seen.get(dedupe_key)
    if first is None:
        seen[dedupe_key] = case_id
        return "accepted_once"
    return "rejected_duplicate"


def _legacy_by_case(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    records = load_valid_legacy_results(path)
    return {str(record["case_id"]): record for record in records}


def _expected_from_legacy(record: Mapping[str, Any]) -> dict[str, Any]:
    result = record.get("result")
    if not isinstance(result, Mapping):
        return {}
    normalized = result.get("normalized_payload")
    if not isinstance(normalized, Mapping):
        normalized = {}
    return {
        "accepted": result.get("accepted"),
        "reason_code": result.get("reason_code"),
        "candidate_type": normalized.get("candidate_type"),
        "symbol": normalized.get("symbol"),
        "side": normalized.get("side"),
        "entry_price": normalized.get("entry_price"),
        "quantity": normalized.get("quantity"),
        "stop_loss": normalized.get("stop_loss"),
        "take_profit": normalized.get("take_profit"),
        "parser_confidence": result.get("parser_confidence"),
        "duplicate_disposition": result.get("duplicate_disposition"),
    }


def _canonical_number(value: Any) -> str | None:
    normalized = canonical_decimal(value)
    if normalized is None:
        return None
    try:
        return str(Decimal(normalized))
    except (InvalidOperation, ValueError):
        return normalized


def _mismatch(
    case_id: str,
    field: str,
    expected_path: str,
    actual_path: str,
    mismatch_class: str = "PARSER_BEHAVIOR_REGRESSION",
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "field": field,
        "mismatch_class": mismatch_class,
        "expected_path": expected_path,
        "actual_path": actual_path,
    }


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"fixture must be a JSON object: {path}")
    return payload


def _schema(name: str) -> dict[str, Any]:
    return json.loads(schema_path(name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
