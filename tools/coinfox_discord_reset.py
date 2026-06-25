#!/usr/bin/env python3
"""Explicit live CoinFox Discord reset helper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.discord.archive import (  # noqa: E402
    BOT_TOKEN_ENV,
    DiscordAPIError,
    DiscordCredentialError,
)
from foxclaw.adapters.discord.reset import (  # noqa: E402
    client_from_env,
    ensure_reset_structure,
    hide_legacy_surface,
    live_permission_report,
    rename_guild,
    revoke_all_invites,
    seed_first_pinned_posts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guild-id", required=True, help="Discord guild/server id")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="check bot permissions needed for reset")
    subparsers.add_parser("revoke-invites", help="revoke every active guild invite")
    subparsers.add_parser(
        "setup-structure",
        help="create Founder Vault, Reset Staging, and public CoinFox categories",
    )
    rename_server = subparsers.add_parser("rename-server", help="rename the Discord server")
    rename_server.add_argument("--name", required=True, help="new Discord server name")
    subparsers.add_parser(
        "hide-legacy-surface",
        help="hide non-CoinFox legacy categories/channels from @everyone",
    )
    subparsers.add_parser(
        "seed-first-pins",
        help="post and pin the first public CoinFox launch notes",
    )

    args = parser.parse_args(argv)
    try:
        client = client_from_env()
        if args.command == "doctor":
            _print_json(live_permission_report(client, args.guild_id))
            return 0
        if args.command == "revoke-invites":
            _print_json(revoke_all_invites(client, args.guild_id))
            return 0
        if args.command == "setup-structure":
            _print_json(ensure_reset_structure(client, args.guild_id))
            return 0
        if args.command == "rename-server":
            _print_json(rename_guild(client, args.guild_id, args.name))
            return 0
        if args.command == "hide-legacy-surface":
            _print_json(hide_legacy_surface(client, args.guild_id))
            return 0
        if args.command == "seed-first-pins":
            _print_json(seed_first_pinned_posts(client, args.guild_id))
            return 0
    except DiscordCredentialError as exc:
        return _fail(str(exc), code=4)
    except DiscordAPIError as exc:
        return _fail(str(exc), code=5)

    return _fail(f"unsupported command: {args.command}", code=2)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def _fail(message: str, *, code: int) -> int:
    redacted = message.replace(BOT_TOKEN_ENV + "=", BOT_TOKEN_ENV + "=<redacted>")
    print(f"coinfox discord reset error: {redacted}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
