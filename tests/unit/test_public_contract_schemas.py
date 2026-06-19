from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from foxclaw.contract.public import PUBLIC_CONTRACT_DIR, SCHEMA_FILES, schema_path

REPO = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO / "tests" / "fixtures" / "public_contract"

SCHEMA_FIXTURES = {
    "public_intelligence_card.schema.json": "public_intelligence_card.valid.json",
    "public_scorecard.schema.json": "public_scorecard.valid.json",
    "attention_receipt.schema.json": "attention_receipt.valid.json",
    "risk_classification.schema.json": "risk_classification.valid.json",
}

FORBIDDEN_TRUE_FLAGS = {
    "can_submit_order",
    "can_submit_orders",
    "can_move_funds",
    "live_execution_allowed",
    "one_click_copy_trade_allowed",
    "can_change_truth",
    "can_change_source_reliability",
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
    elif expected == "number":
        assert isinstance(value, (int, float)) and not isinstance(value, bool), f"{path} must be number"
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


def _walk_public_values(value: Any) -> Any:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_TRUE_FLAGS:
                assert child is False, f"{key} must not grant authority"
            if key == "authority":
                assert child in {"observe_only", "paper_only", "review_priority_only"}
            _walk_public_values(child)
    elif isinstance(value, list):
        for child in value:
            _walk_public_values(child)


def test_public_contract_schemas_are_valid_json():
    assert set(SCHEMA_FILES) == set(SCHEMA_FIXTURES)
    for schema_name in SCHEMA_FIXTURES:
        schema = _load(schema_path(schema_name))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False


def test_public_contract_fixtures_match_required_schema_shape():
    for schema_name, fixture_name in SCHEMA_FIXTURES.items():
        schema = _load(schema_path(schema_name))
        fixture = _load(FIXTURE_DIR / fixture_name)
        _assert_required_shape(schema, fixture)
        _walk_public_values(fixture)


def test_public_contract_readme_names_every_schema():
    readme = (PUBLIC_CONTRACT_DIR / "README.md").read_text(encoding="utf-8")
    for schema_name in SCHEMA_FIXTURES:
        assert schema_name in readme


def test_unknown_public_contract_schema_is_rejected():
    try:
        schema_path("private_engine_state.schema.json")
    except ValueError as exc:
        assert "unknown public contract schema" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unknown schema name was accepted")
