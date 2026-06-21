#!/usr/bin/env python3
"""Replay sanitized parser-compatibility fixtures through the offline v13 parser."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.market.signals.legacy_v13 import parse_raw_source_event  # noqa: E402

DEFAULT_FIXTURE_DIR = REPO / "tests" / "fixtures" / "parser_v1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fixture", help="single sanitized fixture JSON path")
    source.add_argument(
        "--fixtures-dir",
        default=None,
        help="directory of sanitized fixture JSON files",
    )
    parser.add_argument("--json", action="store_true", help="emit safe JSON")
    args = parser.parse_args(argv)

    fixtures = _fixture_paths(Path(args.fixture) if args.fixture else Path(args.fixtures_dir))
    records = []
    for path in fixtures:
        envelope = _load(path)
        fixture_id = str(envelope.get("fixture_id") or path.stem)
        result = parse_raw_source_event(envelope, mode="fixture")
        records.append(result.to_report_dict(fixture_id=fixture_id))

    payload: dict[str, Any] = {
        "schema_version": "parser_compat_replay.v0",
        "fixture_count": len(records),
        "records": records,
        "writes": [],
        "network": False,
        "coinfox": False,
        "execution_authority": False,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str))
    else:
        for record in records:
            print(
                f"{record['fixture_id']}: {record['status']} "
                f"{record['reason_code']} {record['parser_version']}"
            )
        print(f"fixtures: {len(records)}")
    return 0


def _fixture_paths(path: Path | None) -> list[Path]:
    if path is None:
        path = DEFAULT_FIXTURE_DIR
    path = path.resolve()
    if path.is_dir():
        return sorted(item for item in path.glob("*.json") if item.is_file())
    if path.is_file():
        return [path]
    raise SystemExit(f"fixture path not found: {path}")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"fixture must be a JSON object: {path}")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
