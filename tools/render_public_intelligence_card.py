#!/usr/bin/env python3
"""Render one public intelligence card as Markdown."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.contract.public.card import render_public_intelligence_card_markdown  # noqa: E402

DEFAULT_CARD = REPO / "tests" / "fixtures" / "public_contract" / "good_signal_bad_trade.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--card", default=str(DEFAULT_CARD), help="public card JSON path")
    parser.add_argument("--fixture", action="store_true", help="render the canonical fixture")
    args = parser.parse_args(argv)

    card_path = DEFAULT_CARD if args.fixture else Path(args.card)
    card = json.loads(card_path.read_text(encoding="utf-8"))
    print(render_public_intelligence_card_markdown(card))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
