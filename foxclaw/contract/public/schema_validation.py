"""Narrow stdlib JSON Schema checks for frozen public contract schemas."""
from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Mapping


def validate_json_schema(value: Any, schema: Mapping[str, Any], *, path: str = "$") -> None:
    """Validate ``value`` against the schema keywords used by public contracts."""
    _validate_type(value, schema.get("type"), path)

    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path}: const")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: enum")

    if isinstance(value, Mapping):
        _validate_object(value, schema, path)
    elif isinstance(value, list):
        _validate_array(value, schema, path)

    _validate_numeric_bounds(value, schema, path)
    _validate_string_bounds(value, schema, path)
    _validate_format(value, schema, path)
    _validate_composition(value, schema, path)


def _validate_object(value: Mapping[str, Any], schema: Mapping[str, Any], path: str) -> None:
    properties = schema.get("properties", {})
    if not isinstance(properties, Mapping):
        properties = {}

    for key in schema.get("required", ()):
        if key not in value:
            raise ValueError(f"{_child_path(path, str(key))}: required")

    if schema.get("additionalProperties") is False:
        for key in sorted(set(value) - set(properties)):
            raise ValueError(f"{_child_path(path, str(key))}: additionalProperties")
    elif isinstance(schema.get("additionalProperties"), Mapping):
        child_schema = schema["additionalProperties"]
        for key in sorted(set(value) - set(properties)):
            validate_json_schema(value[key], child_schema, path=_child_path(path, str(key)))

    for key, child in properties.items():
        if key in value:
            validate_json_schema(value[key], child, path=_child_path(path, str(key)))


def _validate_array(value: list[Any], schema: Mapping[str, Any], path: str) -> None:
    item_schema = schema.get("items")
    if isinstance(item_schema, Mapping):
        for index, item in enumerate(value):
            validate_json_schema(item, item_schema, path=f"{path}[{index}]")
    elif isinstance(item_schema, list):
        for index, child_schema in enumerate(item_schema[: len(value)]):
            validate_json_schema(value[index], child_schema, path=f"{path}[{index}]")

    if "minItems" in schema and len(value) < int(schema["minItems"]):
        raise ValueError(f"{path}: minItems")
    if "maxItems" in schema and len(value) > int(schema["maxItems"]):
        raise ValueError(f"{path}: maxItems")


def _validate_type(value: Any, expected: Any, path: str) -> None:
    if expected is None:
        return
    allowed = (expected,) if isinstance(expected, str) else tuple(expected)
    if not any(_matches_type(value, item) for item in allowed):
        raise ValueError(f"{path}: type {'|'.join(str(item) for item in allowed)}")


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, Mapping)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _validate_numeric_bounds(value: Any, schema: Mapping[str, Any], path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return
    if "minimum" in schema and value < schema["minimum"]:
        raise ValueError(f"{path}: minimum")
    if "maximum" in schema and value > schema["maximum"]:
        raise ValueError(f"{path}: maximum")


def _validate_string_bounds(value: Any, schema: Mapping[str, Any], path: str) -> None:
    if not isinstance(value, str):
        return
    if "minLength" in schema and len(value) < int(schema["minLength"]):
        raise ValueError(f"{path}: minLength")
    if "maxLength" in schema and len(value) > int(schema["maxLength"]):
        raise ValueError(f"{path}: maxLength")
    if "pattern" in schema and re.search(str(schema["pattern"]), value) is None:
        raise ValueError(f"{path}: pattern")


def _validate_format(value: Any, schema: Mapping[str, Any], path: str) -> None:
    if schema.get("format") != "date-time" or not isinstance(value, str):
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{path}: format date-time") from exc


def _validate_composition(value: Any, schema: Mapping[str, Any], path: str) -> None:
    for child in schema.get("allOf", ()):
        validate_json_schema(value, child, path=path)

    if "anyOf" in schema:
        matches = _composition_matches(value, schema["anyOf"], path)
        if matches == 0:
            raise ValueError(f"{path}: anyOf")

    if "oneOf" in schema:
        matches = _composition_matches(value, schema["oneOf"], path)
        if matches != 1:
            raise ValueError(f"{path}: oneOf")

    if "not" in schema:
        try:
            validate_json_schema(value, schema["not"], path=path)
        except ValueError:
            return
        raise ValueError(f"{path}: not")


def _composition_matches(value: Any, schemas: list[Mapping[str, Any]], path: str) -> int:
    matches = 0
    for child in schemas:
        try:
            validate_json_schema(value, child, path=path)
        except ValueError:
            continue
        matches += 1
    return matches


def _child_path(path: str, key: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
        return f"{path}.{key}"
    return f"{path}[{key!r}]"
