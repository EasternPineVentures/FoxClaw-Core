#!/usr/bin/env python3
"""Run the mention-only CoinFox Discord representative bot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.discord.archive import DiscordAPIError, DiscordCredentialError
from foxclaw.adapters.discord.representative import (
    client_from_env,
    default_state_path,
    load_channel_config,
    run_once,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channels-config", required=True, help="JSON allowlist of public channels")
    parser.add_argument("--state-path", default=None, help="local state file; defaults outside repo")
    parser.add_argument("--send", action="store_true", help="post replies to Discord")
    args = parser.parse_args(argv)

    try:
        client = client_from_env()
        bot_user_id = str(client.me()["id"])
        summary = run_once(
            client,
            bot_user_id=bot_user_id,
            channels=load_channel_config(args.channels_config),
            state_path=Path(args.state_path) if args.state_path else default_state_path(),
            send=args.send,
        )
        summary["mode"] = "send" if args.send else "dry_run"
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except (DiscordCredentialError, DiscordAPIError, ValueError) as exc:
        print(f"coinfox discord rep error: {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
