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
from foxclaw.adapters.market.candidate_projection import project_candidate  # noqa: E402
from foxclaw.intelligence.microscope import (  # noqa: E402
    MicroscopeCandidateNotFoundError,
    assess_candidate,
)
from foxclaw.store.candidate_reader import (  # noqa: E402
    CandidateDatabaseError,
    CandidateDatabaseMissingError,
    CandidateSchemaError,
    ReadOnlyCandidateReader,
)
from foxclaw.store.db import resolve_db  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-id", type=int, help="accepted candidate id")
    parser.add_argument("--db", help="Grove SQLite database path")
    parser.add_argument("--json", action="store_true", help="emit one compact private JSON object")
    parser.add_argument(
        "--private-preview",
        action="store_true",
        help="explicitly render a private, not-published, paper-only preview",
    )
    parser.add_argument(
        "--list-recent",
        action="store_true",
        help="list safe recent accepted-candidate metadata for operator selection",
    )
    parser.add_argument("--limit", type=int, default=10, help="recent candidate list limit")
    args = parser.parse_args(argv)

    db_path = resolve_db(args.db)
    if args.list_recent:
        if args.candidate_id is not None:
            parser.error("--candidate-id cannot be used with --list-recent")
        try:
            rows = ReadOnlyCandidateReader(db_path).iter_after(candidate_id=0, limit=args.limit)
        except CandidateDatabaseMissingError as exc:
            return _fail(str(exc), json_mode=args.json, code=3)
        except (CandidateSchemaError, CandidateDatabaseError) as exc:
            return _fail(str(exc), json_mode=args.json, code=5)
        listing = _safe_candidate_listing(rows)
        if args.json:
            print(json.dumps(listing, sort_keys=True, separators=(",", ":"), default=str))
        else:
            print(_render_recent_listing(listing))
        return 0

    if args.candidate_id is None:
        parser.error("--candidate-id is required unless --list-recent is used")

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


def _safe_candidate_listing(rows: list[dict[str, object]]) -> list[dict[str, Any]]:
    listing: list[dict[str, Any]] = []
    for row in rows:
        item: dict[str, Any] = {
            "candidate_id": row.get("candidate_id"),
            "created_at": row.get("created_at"),
            "publication_class": "INTERNAL_ONLY",
        }
        try:
            projection = project_candidate(row)
        except CandidateProjectionError:
            item.update(
                {
                    "candidate_type": "unavailable",
                    "subject": "unavailable",
                    "direction_or_outcome": "unavailable",
                    "projection_status": "unavailable",
                }
            )
        else:
            item.update(
                {
                    "candidate_type": projection.candidate_type or "unavailable",
                    "subject": projection.subject or projection.symbol or "unavailable",
                    "direction_or_outcome": (
                        projection.direction_or_outcome or projection.side or "unavailable"
                    ),
                    "projection_status": "ok",
                    "sanitized_fields": list(projection.sanitized_fields),
                }
            )
        listing.append(item)
    return listing


def _render_recent_listing(listing: list[dict[str, Any]]) -> str:
    if not listing:
        return "No accepted candidates found."
    lines = ["PRIVATE CANDIDATE LIST", "NOT PUBLISHED", ""]
    for item in listing:
        lines.append(
            " | ".join(
                [
                    f"id={item['candidate_id']}",
                    f"created_at={_display(item.get('created_at'))}",
                    f"type={_display(item.get('candidate_type'))}",
                    f"subject={_display(item.get('subject'))}",
                    f"direction={_display(item.get('direction_or_outcome'))}",
                    f"publication_class={item['publication_class']}",
                ]
            )
        )
    return "\n".join(lines)


def _display(value: Any) -> str:
    text = str(value or "unavailable")
    return " ".join(text.split())


if __name__ == "__main__":
    raise SystemExit(main())
