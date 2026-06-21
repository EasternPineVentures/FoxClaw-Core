from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from foxclaw.adapters.market.signals.legacy_v13 import PARSER_VERSION, parse_raw_source_event
from foxclaw.contract.internal import schema_path
from foxclaw.contract.public.schema_validation import validate_json_schema
from tools.compare_parser_parity import compare_fixture_dir
from tools.validate_parser_legacy_results import validate_legacy_jsonl

REPO = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO / "tests" / "fixtures" / "parser_v1"
LEGACY_JSONL = FIXTURE_DIR / "legacy_parser_results.valid.jsonl"


def _fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _schemas() -> dict[str, dict[str, Any]]:
    return {
        name: json.loads(schema_path(name).read_text(encoding="utf-8"))
        for name in (
            "raw_source_event.schema.json",
            "parse_attempt.schema.json",
            "accepted_candidate.schema.json",
            "parser_rejection.schema.json",
        )
    }


def test_parser_accepts_sanitized_v13_trade_signal_contracts():
    result = parse_raw_source_event(
        _fixture("accepted_btc_long.json"),
        mode="fixture",
        generated_at="2026-06-20T12:30:00+00:00",
    )
    schemas = _schemas()

    assert result.accepted is True
    assert result.reason_code == "accepted_trade_signal"
    assert result.parse_attempt["parser"]["version"] == PARSER_VERSION
    assert result.normalized_payload == {
        "candidate_type": "trade_signal",
        "symbol": "BTC/USD",
        "subject": "BTC/USD",
        "side": "long",
        "direction_or_outcome": "long",
        "entry_price": 65000,
        "quantity": 1,
        "stop_loss": 64000,
        "take_profit": 68000,
        "summary": "Sanitized v13-compatible trade signal.",
    }
    assert result.accepted_candidate is not None
    assert result.accepted_candidate["admission_policy_version"] == "parser_admission_v0"
    assert result.accepted_candidate["parser_version"] == PARSER_VERSION
    assert result.accepted_candidate["confidence"] == result.parser_confidence / 100
    assert "edge" not in result.accepted_candidate
    assert "risk" not in result.accepted_candidate

    validate_json_schema(result.raw_source_event, schemas["raw_source_event.schema.json"])
    validate_json_schema(result.parse_attempt, schemas["parse_attempt.schema.json"])
    validate_json_schema(result.accepted_candidate, schemas["accepted_candidate.schema.json"])


def test_parser_rejections_preserve_exact_reason_codes_and_contracts():
    cases = {
        "rejected_context_only.json": "context_only",
        "rejected_missing_stop.json": "missing_stop",
        "rejected_prompt_injection.json": "prompt_injection_attempt",
    }
    rejection_schema = _schemas()["parser_rejection.schema.json"]
    for filename, reason in cases.items():
        result = parse_raw_source_event(_fixture(filename), mode="fixture")
        assert result.accepted is False
        assert result.reason_code == reason
        assert result.parse_attempt["rejection_reason"] == reason
        assert result.parser_rejection is not None
        assert result.parser_rejection["reason_code"] == reason
        validate_json_schema(result.parser_rejection, rejection_schema)


def test_dedupe_uses_normalized_content_hash_plus_source_not_message_lineage():
    first = parse_raw_source_event(_fixture("accepted_btc_long.json"), mode="fixture")
    duplicate = parse_raw_source_event(
        _fixture("accepted_btc_long_duplicate.json"),
        mode="fixture",
    )
    assert first.raw_source_event["content"]["content_hash"] == duplicate.raw_source_event["content"]["content_hash"]
    assert first.dedupe_key == duplicate.dedupe_key
    assert first.private_lineage["message_lineage"] != duplicate.private_lineage["message_lineage"]

    changed_source = deepcopy(_fixture("accepted_btc_long_duplicate.json"))
    changed_source["raw_source_event"]["private_source_ref"]["source_ref_id"] = "source_hash_other"
    changed = parse_raw_source_event(changed_source, mode="fixture")
    assert changed.raw_source_event["content"]["content_hash"] == first.raw_source_event["content"]["content_hash"]
    assert changed.dedupe_key != first.dedupe_key


def test_deterministic_ids_are_stable_across_reruns():
    fixture = _fixture("accepted_btc_long.json")
    first = parse_raw_source_event(fixture, mode="fixture", generated_at="2026-06-20T12:30:00+00:00")
    second = parse_raw_source_event(fixture, mode="fixture", generated_at="2026-06-20T12:30:01+00:00")

    assert first.parse_attempt["parse_attempt_id"] == second.parse_attempt["parse_attempt_id"]
    assert first.accepted_candidate is not None
    assert second.accepted_candidate is not None
    assert first.accepted_candidate["accepted_candidate_id"] == second.accepted_candidate["accepted_candidate_id"]
    assert first.accepted_candidate["evidence_hash"] == second.accepted_candidate["evidence_hash"]


def test_parity_report_matches_committed_fixture_expectations():
    report = compare_fixture_dir(FIXTURE_DIR)

    assert report["schema_version"] == "parser_parity_report.v1"
    assert report["fixture_count"] == 5
    assert report["legacy_result_count"] == 0
    assert report["matched"] == 5
    assert report["mismatch_count"] == 0
    assert report["mismatches"] == []
    assert {record["duplicate_disposition"] for record in report["records"]} >= {
        "accepted_once",
        "rejected_duplicate",
    }
    assert report["writes"] == []
    assert report["network"] is False
    assert report["coinfox"] is False
    assert report["execution_authority"] is False


def test_legacy_parser_jsonl_validates_and_compares_to_v2_replay():
    validation = validate_legacy_jsonl(LEGACY_JSONL)
    assert validation["valid"] is True
    assert validation["records"] == 5
    assert validation["errors"] == []

    report = compare_fixture_dir(FIXTURE_DIR, legacy_jsonl=LEGACY_JSONL)
    assert report["schema_version"] == "parser_parity_report.v1"
    assert report["fixture_count"] == 5
    assert report["legacy_result_count"] == 5
    assert report["matched"] == 5
    assert report["mismatch_count"] == 0
    validate_json_schema(
        report,
        json.loads(schema_path("parser_parity_report.schema.json").read_text(encoding="utf-8")),
    )


def test_replay_and_compare_clis_are_offline_and_json_safe():
    replay = subprocess.run(
        [
            sys.executable,
            "tools/replay_parser_compat.py",
            "--fixtures-dir",
            str(FIXTURE_DIR),
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    replay_payload = json.loads(replay.stdout)
    assert replay_payload["fixture_count"] == 5
    assert replay_payload["writes"] == []
    assert replay_payload["network"] is False
    assert replay_payload["coinfox"] is False

    parity = subprocess.run(
        [
            sys.executable,
            "tools/compare_parser_parity.py",
            "--fixtures-dir",
            str(FIXTURE_DIR),
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    parity_payload = json.loads(parity.stdout)
    assert parity_payload["mismatch_count"] == 0
    assert parity_payload["standard"]["numeric"] == "canonical_decimal"

    validation = subprocess.run(
        [
            sys.executable,
            "tools/validate_parser_legacy_results.py",
            "--jsonl",
            str(LEGACY_JSONL),
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    validation_payload = json.loads(validation.stdout)
    assert validation_payload["valid"] is True
    assert validation_payload["records"] == 5

    parity_with_legacy = subprocess.run(
        [
            sys.executable,
            "tools/compare_parser_parity.py",
            "--legacy-jsonl",
            str(LEGACY_JSONL),
            "--fixtures-dir",
            str(FIXTURE_DIR),
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    parity_with_legacy_payload = json.loads(parity_with_legacy.stdout)
    assert parity_with_legacy_payload["legacy_result_count"] == 5
    assert parity_with_legacy_payload["mismatch_count"] == 0
