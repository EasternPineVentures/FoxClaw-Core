#!/usr/bin/env python3
"""Read-only CoinFox Discord archive helper."""

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
    DiscordArchiveError,
    DiscordCredentialError,
    DiscordRestClient,
    bot_token_from_env,
    doctor,
    export_channel,
    export_channel_pins,
    snapshot_guild,
    stop_gate_report,
    verify_checksums,
    write_checksums,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive-root",
        default=None,
        help="local private archive root outside git",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="inspect local archive and credential state")

    snapshot = subparsers.add_parser("snapshot", help="save read-only guild metadata")
    snapshot.add_argument("--guild-id", required=True, help="Discord guild/server id")

    export = subparsers.add_parser("export-channel", help="export one channel through bot REST")
    export.add_argument("--channel-id", required=True, help="Discord channel id")
    export.add_argument(
        "--bucket",
        required=True,
        choices=(
            "founder-notes",
            "signal-history",
            "important-decisions",
            "pins",
            "server-snapshot",
        ),
        help="archive export bucket",
    )
    export.add_argument("--max-messages", type=int, default=1000, help="maximum messages to fetch")
    export.add_argument(
        "--no-attachments",
        action="store_true",
        help="skip attachment and image downloads",
    )

    export_pins = subparsers.add_parser(
        "export-pins", help="export pinned messages for one channel through bot REST"
    )
    export_pins.add_argument("--channel-id", required=True, help="Discord channel id")
    export_pins.add_argument(
        "--no-attachments",
        action="store_true",
        help="skip pin attachment and image downloads",
    )

    subparsers.add_parser("checksum", help="write checksums.sha256 for local archive")
    subparsers.add_parser("verify", help="verify checksums.sha256")
    subparsers.add_parser("stop-gate", help="report local cleanup stop-gate status")

    args = parser.parse_args(argv)
    archive_root = Path(args.archive_root) if args.archive_root else _default_archive_root()

    try:
        if args.command == "doctor":
            _print_json(doctor(archive_root))
            return 0
        if args.command == "checksum":
            _print_json(write_checksums(archive_root))
            return 0
        if args.command == "verify":
            failures = verify_checksums(archive_root)
            _print_json({"ok": not failures, "failures": failures})
            return 0 if not failures else 7
        if args.command == "stop-gate":
            report = stop_gate_report(archive_root)
            _print_json(report)
            return 0 if report["ready"] else 8

        token = bot_token_from_env()
        client = DiscordRestClient(token=token)
        if args.command == "snapshot":
            _print_json(snapshot_guild(archive_root, client, args.guild_id))
            return 0
        if args.command == "export-channel":
            _print_json(
                export_channel(
                    archive_root,
                    client,
                    channel_id=args.channel_id,
                    bucket=args.bucket,
                    max_messages=args.max_messages,
                    include_attachments=not args.no_attachments,
                )
            )
            return 0
        if args.command == "export-pins":
            _print_json(
                export_channel_pins(
                    archive_root,
                    client,
                    channel_id=args.channel_id,
                    include_attachments=not args.no_attachments,
                )
            )
            return 0
    except DiscordCredentialError as exc:
        return _fail(str(exc), code=4)
    except (DiscordAPIError, DiscordArchiveError, ValueError) as exc:
        return _fail(str(exc), code=5)

    return _fail(f"unsupported command: {args.command}", code=2)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def _fail(message: str, *, code: int) -> int:
    redacted = message.replace(BOT_TOKEN_ENV + "=", BOT_TOKEN_ENV + "=<redacted>")
    print(f"coinfox discord archive error: {redacted}", file=sys.stderr)
    return code


def _default_archive_root() -> Path:
    return Path.home() / "CoinFox_Discord_Archive_2026-06-24"


if __name__ == "__main__":
    raise SystemExit(main())
