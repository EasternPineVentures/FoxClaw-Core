#!/usr/bin/env python3
"""Submit and validate trusted Forecast Desk evidence packets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.event_contracts.intake import (  # noqa: E402
    SUBMIT_EVIDENCE_CAPABILITY,
    TrustedSubmitter,
    packet_to_dossier_evidence,
    submit_evidence_packet,
    validate_evidence_packet,
)
from foxclaw.adapters.event_contracts.markets import to_jsonable  # noqa: E402
from foxclaw.adapters.event_contracts.storage.repositories import ForecastRepository  # noqa: E402


def fixture_submission() -> tuple[TrustedSubmitter, dict]:
    submitter = TrustedSubmitter(
        submitter_id="founder",
        display_name="Founder",
        trust_tier="founder",
        capabilities=(SUBMIT_EVIDENCE_CAPABILITY,),
    )
    raw = {
        "market_id": "KXFOOTBALL-TRUSTED-FIXTURE",
        "source_id": "official-injury-report",
        "title": "Official injury report fixture",
        "url": "https://example.invalid/official-injury-report",
        "source_type": "official",
        "source_classification": "public",
        "independence_group": "official-team-report",
        "claims": [
            "The player availability note was published by an official public source.",
            "The packet is context only and does not set a forecast probability.",
        ],
    }
    return submitter, raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true", help="use deterministic fixture input")
    parser.add_argument("--db", help="Forecast Desk SQLite DB path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--submitter-id")
    parser.add_argument("--display-name")
    parser.add_argument("--trust-tier", default="trusted_analyst")
    parser.add_argument("--market-id")
    parser.add_argument("--source-id")
    parser.add_argument("--title")
    parser.add_argument("--url")
    parser.add_argument("--source-type", default="public")
    parser.add_argument("--source-classification", default="public")
    parser.add_argument("--claim", action="append", dest="claims")
    parser.add_argument("--nonpublic", action="store_true")
    parser.add_argument("--seen-duplicate-key", action="append", default=[])
    args = parser.parse_args(argv)

    if args.fixture:
        submitter, raw = fixture_submission()
    else:
        submitter = TrustedSubmitter(
            submitter_id=_required(args.submitter_id, "--submitter-id"),
            display_name=args.display_name or _required(args.submitter_id, "--submitter-id"),
            trust_tier=args.trust_tier,
            capabilities=(SUBMIT_EVIDENCE_CAPABILITY,),
        )
        raw = {
            "market_id": _required(args.market_id, "--market-id"),
            "source_id": args.source_id,
            "title": args.title,
            "url": _required(args.url, "--url"),
            "source_type": args.source_type,
            "source_classification": args.source_classification,
            "public": not args.nonpublic,
            "claims": args.claims or [],
        }

    packet = submit_evidence_packet(submitter, raw)
    validation = validate_evidence_packet(
        packet,
        seen_duplicate_keys=tuple(args.seen_duplicate_key),
    )
    repo = ForecastRepository(args.db)
    repo.init_db()
    repo.record_evidence_packet(packet)
    repo.record_intake_validation(validation)
    payload = {
        "mode": "PAPER",
        "status": validation.status,
        "accepted_for_dossier": validation.accepted_for_dossier,
        "packet_id": packet.packet_id,
        "validation_id": validation.validation_id,
        "authority": {
            "authority_level": packet.authority_level,
            "can_set_probability": packet.can_set_probability,
            "can_publish": packet.can_publish,
            "can_enter_paper": packet.can_enter_paper,
            "can_submit_order": packet.can_submit_order,
            "can_move_funds": packet.can_move_funds,
            "live_execution_allowed": packet.live_execution_allowed,
            "can_authorize_execution": validation.can_authorize_execution,
        },
        "packet": packet,
        "validation": validation,
        "dossier_evidence": packet_to_dossier_evidence(packet),
        "counts": repo.counts(),
    }
    if args.json:
        print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
    else:
        print(f"packet_id: {packet.packet_id}")
        print(f"validation_id: {validation.validation_id}")
        print(f"status: {validation.status}")
        print(f"accepted_for_dossier: {validation.accepted_for_dossier}")
    return 0


def _required(value: str | None, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise SystemExit(f"{label} is required unless --fixture is used")
    return text


if __name__ == "__main__":
    raise SystemExit(main())
