#!/usr/bin/env python3
"""Validate A2 legacy parser-result JSONL against parser_legacy_result.v1."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.contract.internal import schema_path  # noqa: E402
from foxclaw.contract.public.schema_validation import validate_json_schema  # noqa: E402

SCHEMA_VERSION = "parser_legacy_validation.v1"

FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"discord(?:app)?\.com/channels", re.I),
    re.compile(r"discord\.gg/", re.I),
    re.compile(r"\b(?:user|channel|server|guild|message)_id\s*[:=]?\s*\d{5,}", re.I),
    re.compile(r"<[@#]!?\d{5,}>", re.I),
    re.compile(r"\b(?:USER_TOKEN|NORMAL_USER_TOKEN)\b", re.I),
    re.compile(r"\b(?:sk-[A-Za-z0-9]{12,}|xox[baprs]-[A-Za-z0-9-]+)\b", re.I),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", required=True, help="legacy_parser_results.jsonl path")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    summary = validate_legacy_jsonl(Path(args.jsonl))
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":"), default=str))
    elif summary["valid"]:
        print(f"valid parser_legacy_result.v1 records: {summary['records']}")
    else:
        print(f"invalid parser legacy JSONL: {summary['error_count']} errors", file=sys.stderr)
        for error in summary["errors"]:
            print(f"line {error['line']}: {error['path']} {error['code']}", file=sys.stderr)
    return 0 if summary["valid"] else 1


def validate_legacy_jsonl(path: Path) -> dict[str, Any]:
    """Return a sanitized validation summary for a legacy result JSONL file."""
    schema = _schema("parser_legacy_result.schema.json")
    errors: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()

    for line_no, payload in _iter_jsonl(path, errors):
        if payload is None:
            continue
        try:
            validate_json_schema(payload, schema)
        except ValueError as exc:
            errors.append(_error(line_no, _path_from_schema_error(exc), "schema"))
            continue
        case_id = str(payload.get("case_id") or "")
        if case_id in seen_case_ids:
            errors.append(_error(line_no, "$.case_id", "duplicate_case_id"))
        seen_case_ids.add(case_id)
        for value_path, value in _walk_string_values(payload):
            for pattern in FORBIDDEN_VALUE_PATTERNS:
                if pattern.search(value):
                    errors.append(_error(line_no, value_path, "private_or_secret_value"))
                    break
        records.append(payload)

    return {
        "schema_version": SCHEMA_VERSION,
        "path": str(path),
        "records": len(records),
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
    }


def load_valid_legacy_results(path: Path) -> list[dict[str, Any]]:
    """Load schema-valid legacy parser results or raise a sanitized ValueError."""
    summary = validate_legacy_jsonl(path)
    if not summary["valid"]:
        first = summary["errors"][0] if summary["errors"] else {"line": 0, "path": "$", "code": "invalid"}
        raise ValueError(
            "legacy parser JSONL failed validation: "
            f"line {first['line']} {first['path']} {first['code']}"
        )
    return [payload for _, payload in _iter_jsonl(path, []) if payload is not None]


def _iter_jsonl(
    path: Path,
    errors: list[dict[str, Any]],
) -> Iterable[tuple[int, dict[str, Any] | None]]:
    if not path.exists():
        errors.append(_error(0, "$", "file_not_found"))
        return
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            errors.append(_error(index, "$", "json_decode"))
            yield index, None
            continue
        if not isinstance(payload, dict):
            errors.append(_error(index, "$", "object_required"))
            yield index, None
            continue
        yield index, payload


def _walk_string_values(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk_string_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_string_values(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def _error(line: int, path: str, code: str) -> dict[str, Any]:
    return {"line": int(line), "path": path, "code": code}


def _path_from_schema_error(exc: ValueError) -> str:
    text = str(exc)
    if ":" in text:
        return text.split(":", 1)[0]
    return "$"


def _schema(name: str) -> dict[str, Any]:
    return json.loads(schema_path(name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
