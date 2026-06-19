#!/usr/bin/env python3
"""Export deterministic public intelligence files for CoinFox."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.contract.public.export import (  # noqa: E402
    build_export_manifest,
    load_fixture_cards,
    load_fixture_outcomes,
    write_coinfox_public_export,
)

DEFAULT_FIXTURE_DIR = REPO / "tests" / "fixtures" / "public_contract"
DEFAULT_OUTPUT_DIR = REPO / "runtime_exports" / "coinfox"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true", help="export checked-in fixture cards")
    parser.add_argument("--fixture-dir", default=str(DEFAULT_FIXTURE_DIR), help="fixture directory")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR), help="output directory")
    parser.add_argument("--no-write", action="store_true", help="print manifest without writing files")
    args = parser.parse_args(argv)

    if not args.fixture:
        parser.error("only --fixture export is implemented until live parser parity lands")

    cards = load_fixture_cards(args.fixture_dir)
    outcomes = load_fixture_outcomes(args.fixture_dir)
    if args.no_write:
        print(json.dumps(build_export_manifest(cards, outcomes), indent=2, sort_keys=True))
        return 0

    paths = write_coinfox_public_export(cards, outcomes, args.output)
    print(
        json.dumps(
            {
                "output_dir": str(Path(args.output)),
                "files": {key: str(path) for key, path in paths.items()},
                "card_count": len(cards),
                "outcome_count": len(outcomes),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
