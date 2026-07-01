from __future__ import annotations

import json
from pathlib import Path
from copy import deepcopy
from typing import Any

import pytest

from foxclaw.contract.public import (
    PUBLIC_CONTRACT_DIR,
    PUBLIC_CONTRACT_VERSION,
    SCHEMA_FILES,
    manifest,
    schema_path,
)
from foxclaw.contract.public.export import validate_public_card

REPO = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO / "tests" / "fixtures" / "public_contract"
CONTRACT_FIXTURE_DIR = REPO / "tests" / "fixtures" / "contracts"

SCHEMA_FIXTURES = {
    "public_intelligence_card.schema.json": FIXTURE_DIR / "public_intelligence_card.valid.json",
    "public_scorecard.schema.json": FIXTURE_DIR / "public_scorecard.valid.json",
    "attention_receipt.schema.json": FIXTURE_DIR / "attention_receipt.valid.json",
    "coinfox_curated_packet.schema.json": FIXTURE_DIR / "coinfox_curated_packet.valid.json",
    "coinfox_coordination_packet.schema.json": CONTRACT_FIXTURE_DIR / "coinfox_intent.valid.json",
    "risk_classification.schema.json": FIXTURE_DIR / "risk_classification.valid.json",
    "verified_outcome.schema.json": FIXTURE_DIR / "verified_outcome.valid.json",
}

CARD_SCENARIO_FIXTURES = (
    "watch.json",
    "good_signal_bad_trade.json",
    "structured.json",
    "speculative.json",
    "redline.json",
    "reject.json",
)

FORBIDDEN_TRUE_FLAGS = {
    "can_submit_order",
    "can_submit_orders",
    "can_move_funds",
    "live_execution_allowed",
    "one_click_copy_trade_allowed",
    "can_change_truth",
    "can_change_source_reliability",
    "can_promote_evidence",
    "can_alter_edge",
    "can_increase_sizing",
    "can_authorize_execution",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _public_card_fixtures() -> list[dict[str, Any]]:
    names = ("public_intelligence_card.valid.json", *CARD_SCENARIO_FIXTURES)
    return [_load(FIXTURE_DIR / name) for name in names]


def _delete_path(value: dict[str, Any], path: tuple[str, ...]) -> dict[str, Any]:
    clone = deepcopy(value)
    target: dict[str, Any] = clone
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    return clone


def _required_paths(schema: dict[str, Any], prefix: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    paths = [(*prefix, key) for key in schema.get("required", [])]
    for key, child in schema.get("properties", {}).items():
        if child.get("type") == "object":
            paths.extend(_required_paths(child, (*prefix, key)))
    return paths


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


def test_public_contract_manifest_freezes_v1():
    data = manifest()
    assert data["contract_name"] == "foxclaw-public-intelligence"
    assert data["contract_version"] == PUBLIC_CONTRACT_VERSION == "1.0.0"
    assert data["consumer_rule"] == "Consumers must refuse unsupported major versions."
    assert set(data["schemas"]) == {
        "public_intelligence_card",
        "public_scorecard",
        "attention_receipt",
        "coinfox_curated_packet",
        "coinfox_coordination_packet",
        "risk_classification",
        "verified_outcome",
    }


def test_public_contract_fixtures_match_required_schema_shape():
    for schema_name, fixture_path in SCHEMA_FIXTURES.items():
        schema = _load(schema_path(schema_name))
        fixture = _load(fixture_path)
        _assert_required_shape(schema, fixture)
        _walk_public_values(fixture)
        assert fixture["contract_version"] == "1.0.0"


def test_public_card_scenario_fixtures_match_v1_card_schema():
    schema = _load(schema_path("public_intelligence_card.schema.json"))
    for fixture_name in CARD_SCENARIO_FIXTURES:
        fixture = _load(FIXTURE_DIR / fixture_name)
        _assert_required_shape(schema, fixture)
        _walk_public_values(fixture)
        assert fixture["author_display"] == "FoxClaw"
        assert fixture["mode"] == "informational_paper"
        assert fixture["contains_private_source_content"] is False
        assert fixture["public_explanation"]["not_individualized_advice"] is True


def test_validate_public_card_accepts_every_v1_public_card_fixture():
    for fixture in _public_card_fixtures():
        validate_public_card(fixture)


def test_validate_public_card_rejects_each_required_top_level_field_when_missing():
    schema = _load(schema_path("public_intelligence_card.schema.json"))
    card = _load(FIXTURE_DIR / "public_intelligence_card.valid.json")

    for key in schema["required"]:
        with pytest.raises(ValueError, match=rf"^\$\.{key}: required$"):
            validate_public_card(_delete_path(card, (key,)))


def test_validate_public_card_rejects_required_nested_fields_when_missing():
    schema = _load(schema_path("public_intelligence_card.schema.json"))
    card = _load(FIXTURE_DIR / "public_intelligence_card.valid.json")
    nested_required = [path for path in _required_paths(schema) if len(path) > 1]

    assert nested_required
    for path in nested_required:
        dotted = r"\.".join(path)
        with pytest.raises(ValueError, match=rf"^\$\.{dotted}: required$"):
            validate_public_card(_delete_path(card, path))


def test_validate_public_card_rejects_wrong_types_and_bool_is_not_integer():
    card = _load(FIXTURE_DIR / "public_intelligence_card.valid.json")
    wrong_string = deepcopy(card)
    wrong_string["claim"]["summary"] = 123
    with pytest.raises(ValueError, match=r"^\$\.claim\.summary: type string$"):
        validate_public_card(wrong_string)

    wrong_integer = deepcopy(card)
    wrong_integer["snapshot_version"] = True
    with pytest.raises(ValueError, match=r"^\$\.snapshot_version: type integer$"):
        validate_public_card(wrong_integer)


def test_validate_public_card_rejects_invalid_enums_and_consts():
    card = _load(FIXTURE_DIR / "public_intelligence_card.valid.json")
    invalid_enum = deepcopy(card)
    invalid_enum["publication_class"] = "INTERNAL_ONLY"
    with pytest.raises(ValueError, match=r"^\$\.publication_class: enum$"):
        validate_public_card(invalid_enum)

    invalid_const = deepcopy(card)
    invalid_const["contains_private_source_content"] = True
    with pytest.raises(ValueError, match=r"^\$\.contains_private_source_content: const$"):
        validate_public_card(invalid_const)


def test_validate_public_card_rejects_extra_properties_where_schema_forbids_them():
    card = _load(FIXTURE_DIR / "public_intelligence_card.valid.json")
    top_level_extra = deepcopy(card)
    top_level_extra["raw_excerpt"] = "must not cross public boundary"
    with pytest.raises(ValueError, match=r"^\$\.raw_excerpt: additionalProperties$"):
        validate_public_card(top_level_extra)

    nested_extra = deepcopy(card)
    nested_extra["claim"]["source_id"] = "private_source_alpha"
    with pytest.raises(ValueError, match=r"^\$\.claim\.source_id: additionalProperties$"):
        validate_public_card(nested_extra)


def test_validate_public_card_errors_do_not_echo_private_values():
    card = _load(FIXTURE_DIR / "public_intelligence_card.valid.json")
    poisoned = deepcopy(card)
    poisoned["claim"]["summary"] = {"token": "SECRET_PRIVATE_VALUE"}

    with pytest.raises(ValueError) as excinfo:
        validate_public_card(poisoned)

    message = str(excinfo.value)
    assert "$.claim.summary: type string" in message
    assert "SECRET_PRIVATE_VALUE" not in message
    assert "token" not in message


def test_resolved_postmortem_fixture_matches_verified_outcome_schema():
    schema = _load(schema_path("verified_outcome.schema.json"))
    fixture = _load(FIXTURE_DIR / "resolved_postmortem.json")
    _assert_required_shape(schema, fixture)
    _walk_public_values(fixture)
    assert fixture["outcome_status"] == "resolved"


def test_public_contract_readme_names_every_schema():
    readme = (PUBLIC_CONTRACT_DIR / "README.md").read_text(encoding="utf-8")
    for schema_name in SCHEMA_FIXTURES:
        assert schema_name in readme
    assert "CoinFox must refuse unsupported major versions" in readme


def test_unknown_public_contract_schema_is_rejected():
    try:
        schema_path("private_engine_state.schema.json")
    except ValueError as exc:
        assert "unknown public contract schema" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unknown schema name was accepted")
