#!/usr/bin/env python3
"""Single-instance Forecast Desk watch loop scaffold."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.forecast_desk_doctor import build_status  # noqa: E402


def run_once(*, status_file: Path, lock_file: Path, fixture: bool) -> dict:
    if lock_file.exists():
        raise RuntimeError(f"watch lock already exists: {lock_file}")
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text(str(datetime.now(UTC).timestamp()), encoding="utf-8")
    try:
        status = build_status(fixture=fixture)
        status["watch_ran_at"] = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        status["freshness_receipt"] = {
            "status_file": str(status_file),
            "max_age_seconds": 120,
            "is_fresh": True,
        }
        status_file.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return status
    finally:
        try:
            lock_file.unlink()
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--status-file", default=str(REPO / "runtime" / "forecast_desk" / "status.json"))
    parser.add_argument("--lock-file", default=str(REPO / "runtime" / "forecast_desk" / "watch.lock"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.once:
        raise SystemExit("Phase H watch scaffold requires --once")
    status = run_once(
        status_file=Path(args.status_file),
        lock_file=Path(args.lock_file),
        fixture=args.fixture,
    )
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
