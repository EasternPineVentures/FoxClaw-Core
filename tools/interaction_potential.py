#!/usr/bin/env python3
"""Score CoinFox packet observations for likely user interaction."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.interaction_potential import (  # noqa: E402
    DEFAULT_CONFIG,
    DEFAULT_INTAKE_FIXTURE,
    load_config,
    render_markdown,
    score_intake_payload,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="interaction config JSON path")
    parser.add_argument("--intake", default=str(DEFAULT_INTAKE_FIXTURE), help="packet intake JSON path")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="use deterministic date/time for tests and handoff examples",
    )
    args = parser.parse_args(argv)

    fixture_generated_at = datetime(2026, 7, 1, 15, 0, tzinfo=UTC) if args.fixture else None
    config = load_config(args.config)
    payload = json.loads(Path(args.intake).read_text(encoding="utf-8"))
    report = score_intake_payload(payload, config=config, generated_at=fixture_generated_at)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
