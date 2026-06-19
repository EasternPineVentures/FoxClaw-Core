from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from foxclaw.contract.internal import INTERNAL_CONTRACT_DIR, SCHEMA_FILES, schema_path

REPO = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO / "tests" / "fixtures" / "internal_contract"

SCHEMA_FIXTURES = {
    "raw_source_event.schema.json": "raw_source_event.valid.json",
    "parse_attempt.schema.json": "parse_attempt.valid.json",
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
        _assert_required_shape(schema, fixture)
        _walk_internal_values(fixture)


def test_internal_fixture_lineage_runs_to_publication_and_outcome():
    raw = _load(FIXTURE_DIR / "raw_source_event.valid.json")
    parse = _load(FIXTURE_DIR / "parse_attempt.valid.json")
    claim = _load(FIXTURE_DIR / "claim_packet.valid.json")
    evidence = _load(FIXTURE_DIR / "evidence_bundle.valid.json")
    tradeability = _load(FIXTURE_DIR / "tradeability_snapshot.valid.json")
    readiness = _load(FIXTURE_DIR / "trade_readiness_verdict.valid.json")
    publication = _load(FIXTURE_DIR / "publication_decision.valid.json")
    outcome = _load(FIXTURE_DIR / "verified_outcome.valid.json")

    assert parse["raw_event_id"] == raw["raw_event_id"]
    assert claim["parse_attempt_id"] == parse["parse_attempt_id"]
    assert claim["claim_packet_id"] in evidence["claim_packet_ids"]
    assert tradeability["evidence_bundle_id"] == evidence["evidence_bundle_id"]
    assert readiness["tradeability_snapshot_id"] == tradeability["tradeability_snapshot_id"]
    assert publication["trade_readiness_verdict_id"] == readiness["trade_readiness_verdict_id"]
    assert outcome["publication_decision_id"] == publication["publication_decision_id"]
    assert publication["publication_class"] == "DERIVATIVE_PUBLIC_SAFE"


def test_internal_contract_readme_and_schemas_name_private_boundaries():
    readme = (INTERNAL_CONTRACT_DIR / "README.md").read_text(encoding="utf-8")
    assert "CoinFox must not consume these objects directly" in readme
    blob = "\n".join(schema_path(name).read_text(encoding="utf-8") for name in SCHEMA_FILES)
    assert "private_source_ref" in blob
    assert "provider_metadata" in blob
    assert "quarantine" in blob


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
