#!/usr/bin/env python3
"""List and run curated FoxClaw operator commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.command_center import (  # noqa: E402
    DEFAULT_CATALOG,
    build_report,
    find_command,
    flatten_commands,
    load_catalog,
    render_command,
    render_markdown,
    run_command,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG), help="command catalog JSON path")
    parser.add_argument("--category", help="only show one command group id")
    parser.add_argument("--search", help="filter commands by text")
    parser.add_argument("--show", help="show one command by id")
    parser.add_argument("--run", help="run one safe runnable command by id")
    parser.add_argument("--list-ids", action="store_true", help="print command ids only")
    parser.add_argument("--all-tools", action="store_true", help="include every tools/*.py script")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args(argv)

    if args.run:
        try:
            return run_command(args.run, args.catalog)
        except (KeyError, ValueError) as exc:
            print(f"[foxclaw-commands] {exc}", file=sys.stderr)
            return 2

    if args.show:
        try:
            command = find_command(args.show, args.catalog)
        except KeyError as exc:
            print(f"[foxclaw-commands] {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(command, indent=2, sort_keys=True))
        else:
            print(render_command(command))
        return 0

    if args.list_ids:
        catalog = load_catalog(args.catalog)
        for command in flatten_commands(catalog):
            print(command["id"])
        return 0

    report = build_report(
        args.catalog,
        category=args.category,
        search=args.search,
        include_all_tools=args.all_tools,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
