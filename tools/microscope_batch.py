#!/usr/bin/env python3
"""Batch private Microscope assessments into safe local staging artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.intelligence.staging import (  # noqa: E402
    DEFAULT_CURSOR_PATH,
    DEFAULT_STAGING_ROOT,
    read_cursor,
    run_microscope_batch,
)
from foxclaw.store.candidate_reader import (  # noqa: E402
    CandidateDatabaseError,
    CandidateDatabaseMissingError,
    CandidateSchemaError,
)
from foxclaw.store.db import resolve_db  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--after-id", type=int, help="internal cursor id to start after")
    parser.add_argument("--limit", type=int, default=50, help="maximum candidates to inspect")
    parser.add_argument("--db", help="Grove SQLite database path")
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_STAGING_ROOT),
        help="local ignored staging root",
    )
    parser.add_argument(
        "--cursor",
        default=str(DEFAULT_CURSOR_PATH),
        help="local ignored internal cursor path",
    )
    parser.add_argument("--run-id", help="operator-supplied staging run id")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="assess only; create no files")
    mode.add_argument(
        "--write-staging",
        action="store_true",
        help="write local staging artifacts and update cursor after durable output",
    )
    args = parser.parse_args(argv)

    db_path = resolve_db(args.db)
    cursor_path = Path(args.cursor)
    after_id = int(args.after_id) if args.after_id is not None else read_cursor(cursor_path)
    dry_run = bool(args.dry_run or not args.write_staging)

    try:
        summary = run_microscope_batch(
            db_path=db_path,
            after_id=after_id,
            limit=args.limit,
            output_root=args.output_root,
            cursor_path=cursor_path,
            dry_run=dry_run,
            write_staging=bool(args.write_staging),
            run_id=args.run_id,
        )
    except CandidateDatabaseMissingError as exc:
        return _fail(str(exc), code=3)
    except (CandidateSchemaError, CandidateDatabaseError) as exc:
        return _fail(str(exc), code=5)
    except ValueError as exc:
        return _fail(str(exc), code=6)

    print(json.dumps(summary, sort_keys=True, separators=(",", ":"), default=str))
    return 0


def _fail(message: str, *, code: int) -> int:
    print(f"microscope batch error: {message}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
