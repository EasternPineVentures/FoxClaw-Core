#!/usr/bin/env python3
"""Export safe static FoxClaw Hunt files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.event_contracts.publication import (  # noqa: E402
    assert_no_private_fields,
    build_public_export,
    write_public_export,
)


def fixture_export():
    return build_public_export(
        [
            {
                "market_id": "KXWIN",
                "side": "yes",
                "verdict": "paper",
                "independent_probability": "0.62",
                "market_probability": "0.43",
                "usable_edge": "0.19",
                "status": "resolved",
                "resolved_outcome": "yes",
                "net_result": "3.99",
                "dossier_hash": "sha256:private",
            },
            {
                "market_id": "KXLOSS",
                "side": "yes",
                "verdict": "paper",
                "independent_probability": "0.58",
                "market_probability": "0.40",
                "usable_edge": "0.18",
                "status": "resolved",
                "resolved_outcome": "no",
                "net_result": "-4.00",
            },
        ],
        scoreboard={"resolved_forecasts": 2, "net_paper_result": "-0.01"},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--write")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.fixture:
        raise SystemExit("Phase G export CLI currently requires --fixture")
    export = fixture_export()
    assert_no_private_fields(export)
    written = {}
    if args.write:
        written = {key: str(value) for key, value in write_public_export(export, args.write).items()}
    payload = {"export": export, "written": written}
    if args.json or not args.write:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
