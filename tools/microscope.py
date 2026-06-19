#!/usr/bin/env python3
"""Build one private, read-only FoxClaw Microscope assessment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.market.candidate_projection import CandidateProjectionError  # noqa: E402
from foxclaw.intelligence.microscope import (  # noqa: E402
    MicroscopeCandidateNotFoundError,
    assess_candidate,
)
from foxclaw.store.candidate_reader import (  # noqa: E402
    CandidateDatabaseError,
    CandidateDatabaseMissingError,
    CandidateSchemaError,
)
from foxclaw.store.db import resolve_db  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-id", type=int, required=True, help="accepted candidate id")
    parser.add_argument("--db", help="Grove SQLite database path")
    parser.add_argument("--json", action="store_true", help="emit one compact private JSON object")
    args = parser.parse_args(argv)

    db_path = resolve_db(args.db)
    try:
        assessment = assess_candidate(candidate_id=args.candidate_id, db_path=str(db_path))
    except MicroscopeCandidateNotFoundError as exc:
        return _fail(str(exc), json_mode=args.json, code=2)
    except CandidateDatabaseMissingError as exc:
        return _fail(str(exc), json_mode=args.json, code=3)
    except CandidateProjectionError as exc:
        return _fail(str(exc), json_mode=args.json, code=4)
    except (CandidateSchemaError, CandidateDatabaseError) as exc:
        return _fail(str(exc), json_mode=args.json, code=5)

    if args.json:
        print(json.dumps(assessment, sort_keys=True, separators=(",", ":"), default=str))
    else:
        print(_render_private_preview(assessment))
    return 0


def _fail(message: str, *, json_mode: bool, code: int) -> int:
    if json_mode:
        print(f"microscope error: {message}", file=sys.stderr)
    else:
        print(f"Microscope error: {message}", file=sys.stderr)
    return code


def _render_private_preview(assessment: dict[str, Any]) -> str:
    projection = assessment["projection"]
    edge = assessment["edge"]
    readiness = assessment["readiness"]
    publication = assessment["publication"]
    contract = assessment["contract"]
    lines = [
        "PRIVATE PREVIEW",
        "NOT PUBLISHED",
        "PAPER-ONLY",
        "",
        f"Assessment ID: {assessment['assessment_id']}",
        f"CONTRACT VERSION: {contract['version']}",
        f"Subject: {_display(projection.get('subject') or projection.get('symbol'))}",
        f"Direction: {_display(projection.get('direction_or_outcome') or projection.get('side'))}",
        f"PUBLICATION CLASS: {publication['publication_class']}",
        f"Published: {str(assessment['published']).lower()}",
        f"Paper ready: {str(assessment['paper_ready']).lower()}",
        f"Live ready: {str(assessment['live_ready']).lower()}",
        f"Readiness verdict: {readiness['verdict']}",
        (
            "Edge: available "
            f"(observations={edge['observation_count']}, prob_edge={edge['verdict']['prob_edge']})"
            if edge["available"]
            else f"Edge: unavailable ({edge['reason']}, observations={edge['observation_count']})"
        ),
        f"Gate tier: {assessment['gate']['tier']}",
    ]
    return "\n".join(lines)


def _display(value: Any) -> str:
    text = str(value or "unavailable")
    return " ".join(text.split())


if __name__ == "__main__":
    raise SystemExit(main())
