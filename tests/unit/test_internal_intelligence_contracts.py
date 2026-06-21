from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from foxclaw.contract.internal import INTERNAL_CONTRACT_DIR, SCHEMA_FILES, schema_path
from foxclaw.contract.public.schema_validation import validate_json_schema

REPO = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO / "tests" / "fixtures" / "internal_contract"

SCHEMA_FIXTURES = {
    "raw_source_event.schema.json": "raw_source_event.valid.json",
    "parse_attempt.schema.json": "parse_attempt.valid.json",
    "accepted_candidate.schema.json": "accepted_candidate.valid.json",
    "parser_rejection.schema.json": "parser_rejection.valid.json",
    "parser_legacy_result.schema.json": "parser_legacy_result.valid.json",
    "parser_parity_report.schema.json": "parser_parity_report.valid.json",
    "claim_packet.schema.json": "claim_packet.valid.json",
    "evidence_bundle.schema.json": "evidence_bundle.valid.json",
    "attention_aggregate.schema.json": "attention_aggregate.valid.json",
    "tradeability_snapshot.schema.json": "tradeability_snapshot.valid.json",
    "trade_readiness_verdict.schema.json": "trade_readiness_verdict.valid.json",
    "publication_decision.schema.json": "publication_decision.valid.json",
    "verified_outcome.schema.json": "verified_outcome.valid.json",
}

FORBIDDEN_TRUE_FLAGS = {
    "can_change_truth",
    "can_change_source_reliability",
    "can_alter_edge",
    "can_increase_sizing",
    "can_authorize_execution",
    "can_submit_order",
    "can_move_funds",
    "live_execution_allowed",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_type(value: Any, expected: str, path: str) -> None:
    if expected == "object":
        assert isinstance(value, dict), f"{path} must be object"
    elif expected == "array":
        assert isinstance(value, list), f"{path} must be array"
    elif expected == "string":
        assert isinstance(value, str), f"{path} must be string"
    elif expected == "integer":
        assert isinstance(value, int) and not isinstance(value, bool), f"{path} must be integer"
    elif expected == "boolean":
        assert isinstance(value, bool), f"{path} must be boolean"


def _assert_required_shape(schema: dict[str, Any], value: Any, path: str = "$") -> None:
    schema_type = schema.get("type")
    if isinstance(schema_type, str):
        _assert_type(value, schema_type, path)
    if "const" in schema:
        assert value == schema["const"], f"{path} must equal const {schema['const']!r}"
    if "enum" in schema:
        assert value in schema["enum"], f"{path} must be one of {schema['enum']!r}"
    if schema_type == "object":
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            assert key in value, f"{path}.{key} is required"
        if schema.get("additionalProperties") is False:
            extras = set(value) - set(properties)
            assert not extras, f"{path} has unexpected keys {sorted(extras)!r}"
        for key, child in properties.items():
            if key in value:
                _assert_required_shape(child, value[key], f"{path}.{key}")
    elif schema_type == "array":
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _assert_required_shape(item_schema, item, f"{path}[{index}]")


def _walk_internal_values(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_TRUE_FLAGS:
                assert child is False, f"{key} must not grant authority"
            _walk_internal_values(child)
    elif isinstance(value, list):
        for child in value:
            _walk_internal_values(child)


def test_internal_contract_schemas_are_valid_json():
    assert set(SCHEMA_FILES) == set(SCHEMA_FIXTURES)
    for schema_name in SCHEMA_FIXTURES:
        schema = _load(schema_path(schema_name))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False


def test_internal_contract_fixtures_match_required_schema_shape():
    for schema_name, fixture_name in SCHEMA_FIXTURES.items():
        schema = _load(schema_path(schema_name))
        fixture = _load(FIXTURE_DIR / fixture_name)
        validate_json_schema(fixture, schema)
        _assert_required_shape(schema, fixture)
        _walk_internal_values(fixture)


def test_internal_fixture_lineage_runs_from_parser_to_publication_and_outcome():
    raw = _load(FIXTURE_DIR / "raw_source_event.valid.json")
    parse = _load(FIXTURE_DIR / "parse_attempt.valid.json")
    candidate = _load(FIXTURE_DIR / "accepted_candidate.valid.json")
    rejection = _load(FIXTURE_DIR / "parser_rejection.valid.json")
    claim = _load(FIXTURE_DIR / "claim_packet.valid.json")
    evidence = _load(FIXTURE_DIR / "evidence_bundle.valid.json")
    tradeability = _load(FIXTURE_DIR / "tradeability_snapshot.valid.json")
    readiness = _load(FIXTURE_DIR / "trade_readiness_verdict.valid.json")
    publication = _load(FIXTURE_DIR / "publication_decision.valid.json")
    outcome = _load(FIXTURE_DIR / "verified_outcome.valid.json")

    assert parse["raw_event_id"] == raw["raw_event_id"]
    assert parse["lineage"]["raw_event_id"] == raw["raw_event_id"]
    assert candidate["raw_event_id"] == raw["raw_event_id"]
    assert candidate["parse_attempt_id"] == parse["parse_attempt_id"]
    assert candidate["lineage"]["content_hash"] == raw["content"]["content_hash"]
    assert rejection["raw_event_id"] == raw["raw_event_id"]
    assert rejection["lineage"]["content_hash"] == raw["content"]["content_hash"]
    assert claim["parse_attempt_id"] == parse["parse_attempt_id"]
    assert claim["claim_packet_id"] in evidence["claim_packet_ids"]
    assert tradeability["evidence_bundle_id"] == evidence["evidence_bundle_id"]
    assert readiness["tradeability_snapshot_id"] == tradeability["tradeability_snapshot_id"]
    assert publication["trade_readiness_verdict_id"] == readiness["trade_readiness_verdict_id"]
    assert outcome["publication_decision_id"] == publication["publication_decision_id"]
    assert publication["publication_class"] == "DERIVATIVE_PUBLIC_SAFE"


def test_parser_contract_defaults_private_and_internal_only():
    raw = _load(FIXTURE_DIR / "raw_source_event.valid.json")
    parse = _load(FIXTURE_DIR / "parse_attempt.valid.json")

    assert raw["payload_classification"]["contains_private_source_content"] is True
    assert raw["payload_classification"]["redistribution"] == "do_not_export"
    assert raw["publicability"]["publication_class"] == "INTERNAL_ONLY"
    assert raw["publicability"]["public_export_allowed"] is False
    assert raw["synthetic"] is True
    assert parse["accepted"] is True
    assert parse["status"] == "accepted"


def test_parser_rejection_fixture_covers_malformed_payload_contract():
    rejection = _load(FIXTURE_DIR / "parser_rejection.valid.json")

    assert rejection["reason_code"] == "malformed_payload"
    assert rejection["diagnostic_category"] == "malformed_payload"
    assert rejection["retryable"] is False
    assert "raw" not in rejection["safe_diagnostic"].lower()


def test_internal_schema_validation_rejects_bool_for_numeric_fields():
    parse_schema = _load(schema_path("parse_attempt.schema.json"))
    parse = _load(FIXTURE_DIR / "parse_attempt.valid.json")
    parse_bad = deepcopy(parse)
    parse_bad["diagnostics"]["confidence"] = True
    with pytest.raises(ValueError, match=r"^\$\.diagnostics\.confidence: type integer$"):
        validate_json_schema(parse_bad, parse_schema)

    candidate_schema = _load(schema_path("accepted_candidate.schema.json"))
    candidate = _load(FIXTURE_DIR / "accepted_candidate.valid.json")
    candidate_bad = deepcopy(candidate)
    candidate_bad["confidence"] = True
    with pytest.raises(ValueError, match=r"^\$\.confidence: type number$"):
        validate_json_schema(candidate_bad, candidate_schema)


def test_committed_internal_parser_fixtures_hide_private_discord_and_token_patterns():
    forbidden = (
        re.compile(r"discord(?:app)?\.com/channels", re.I),
        re.compile(r"discord\.gg/", re.I),
        re.compile(r"\b(?:user|channel|server|guild|message)_id\s*[:=]?\s*\d{5,}", re.I),
        re.compile(r"<[@#]!?\d{5,}>", re.I),
        re.compile(r"\b(?:token|secret|api[_-]?key|password)\s*[:=]", re.I),
        re.compile(r"\b(?:sk-[A-Za-z0-9]{12,}|xox[baprs]-[A-Za-z0-9-]+)\b", re.I),
        re.compile(r"private_source_alpha", re.I),
    )
    for fixture_path in FIXTURE_DIR.glob("*.json"):
        text = fixture_path.read_text(encoding="utf-8")
        for pattern in forbidden:
            assert not pattern.search(text), f"{fixture_path.name} contains {pattern.pattern}"


def test_parser_migration_docs_reconcile_a2_runtime_inventory():
    docs = [
        REPO / "docs" / "migration" / "discord_parser_port_plan.md",
        REPO / "docs" / "migration" / "discord_parser_fixture_policy.md",
        REPO / "docs" / "migration" / "discord_auth_cutover.md",
        REPO / "docs" / "migration" / "parser_parity_standard.md",
        REPO / "docs" / "handoffs" / "a1_parser_contract_foundation.md",
    ]
    for path in docs:
        assert path.exists(), f"{path} missing"

    combined = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    assert "UNKNOWN_PENDING_A2_INVENTORY" not in combined
    assert "pending_a2_inventory" not in combined
    assert "trading/app/user_ingest.py" in combined
    assert "tools/raw_parser.py" in combined
    assert "src/parsers/signal_parser.py::parse_trade_signal" in combined
    assert "live_raw_parser_admission_v13" in combined
    assert "NORMAL_USER_TOKEN" in combined
    assert "USER_TOKEN" in combined
    assert "deterministic rule-based" in combined
    assert "normalized content hash plus `source_id`" in combined
    assert "watched channels plus watched parent threads" in combined
    assert "raw_events" in combined
    assert "parse_attempts" in combined
    assert "tools/promote_accepted_candidates.py" in combined
    assert "duplicate gateway listeners" in combined
    assert "operator-approved private replay corpus path" in combined
    assert "No normal user token" in combined
    assert "No new live Discord listener" in combined


def test_parser_contract_fixtures_use_verified_v13_identity():
    parse = _load(FIXTURE_DIR / "parse_attempt.valid.json")
    candidate = _load(FIXTURE_DIR / "accepted_candidate.valid.json")
    rejection = _load(FIXTURE_DIR / "parser_rejection.valid.json")

    assert parse["parser"]["version"] == "live_raw_parser_admission_v13"
    assert parse["diagnostics"]["provider_metadata"] == {
        "provider": "rule_based",
        "model": "none",
        "prompt_version": "live_raw_parser_admission_v13",
    }
    assert candidate["parser_version"] == "live_raw_parser_admission_v13"
    assert rejection["parser"]["version"] == "live_raw_parser_admission_v13"


def test_internal_parser_contracts_do_not_carry_stale_a2_unknown_or_provider_failures():
    blob = "\n".join(
        [
            schema_path("raw_source_event.schema.json").read_text(encoding="utf-8"),
            schema_path("accepted_candidate.schema.json").read_text(encoding="utf-8"),
            schema_path("parser_rejection.schema.json").read_text(encoding="utf-8"),
        ]
    )
    assert "UNKNOWN_PENDING_A2_INVENTORY" not in blob
    assert "pending_a2_inventory" not in blob
    assert "provider_timeout" not in blob
    assert "provider_error" not in blob


def test_internal_contract_readme_and_schemas_name_private_boundaries():
    readme = (INTERNAL_CONTRACT_DIR / "README.md").read_text(encoding="utf-8")
    assert "CoinFox must not consume these objects directly" in readme
    blob = "\n".join(schema_path(name).read_text(encoding="utf-8") for name in SCHEMA_FILES)
    assert "private_source_ref" in blob
    assert "provider_metadata" in blob
    assert "quarantine" in blob
    assert "accepted_candidate.schema.json" in SCHEMA_FILES
    assert "parser_rejection.schema.json" in SCHEMA_FILES
    assert "parser_legacy_result.schema.json" in SCHEMA_FILES
    assert "parser_parity_report.schema.json" in SCHEMA_FILES


def test_private_parser_fixture_folders_are_ignored():
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "tests/fixtures/parser_private/" in gitignore
    assert "tests/fixtures/internal_private/" in gitignore


def test_unknown_internal_contract_schema_is_rejected():
    try:
        schema_path("public_intelligence_card.schema.json")
    except ValueError as exc:
        assert "unknown internal contract schema" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unknown schema name was accepted")
