# CoinFox Discord Representative Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a mention-only CoinFox Discord representative bot that answers public-safe company, routing, rules, and risk-boundary questions while refusing trade advice and private-history requests.

**Architecture:** Add a pure-stdlib deterministic representative module plus a CLI runner. The bot polls configured public Discord channels through REST, filters to direct mentions, classifies each mention with a deterministic policy, dry-runs by default, and only posts replies when `--send` is explicitly provided.

**Tech Stack:** Python 3.11+ standard library, existing Discord REST helpers/patterns, pytest fake-client unit tests, `COINFOX_DISCORD_BOT_TOKEN`.

---

## File Structure

- Create `foxclaw/adapters/discord/representative.py`: deterministic policy, knowledge pack, mention gating, REST client, state store, and one-cycle runner.
- Create `tools/coinfox_discord_rep.py`: CLI for dry-run and live send.
- Create `tests/unit/test_coinfox_discord_representative.py`: unit tests with fake Discord client and temp state.
- Modify `docs/CoinFox_Discord_Reset_Operator_Checklist.md`: add operator notes for rep-bot dry-run and live use.

## Task 1: Deterministic Representative Policy

**Files:**
- Create: `foxclaw/adapters/discord/representative.py`
- Test: `tests/unit/test_coinfox_discord_representative.py`

- [ ] **Step 1: Write failing policy tests**

Add this to `tests/unit/test_coinfox_discord_representative.py`:

```python
from foxclaw.adapters.discord import representative as rep


def test_representative_ignores_unmentioned_messages() -> None:
    message = {
        "id": "100",
        "content": "what is CoinFox?",
        "author": {"id": "user_1", "bot": False},
        "mentions": [],
    }

    decision = rep.classify_message(
        message,
        bot_user_id="bot_1",
        channel_name="general",
        allowed_channel_ids={"chan_general"},
        channel_id="chan_general",
    )

    assert decision.action == "ignore"
    assert decision.reason == "not_mentioned"
    assert decision.reply is None


def test_representative_refuses_financial_advice() -> None:
    message = {
        "id": "101",
        "content": "<@bot_1> should I buy BTC right now?",
        "author": {"id": "user_1", "bot": False},
        "mentions": [{"id": "bot_1"}],
    }

    decision = rep.classify_message(
        message,
        bot_user_id="bot_1",
        channel_name="trade-ideas",
        allowed_channel_ids={"chan_trade"},
        channel_id="chan_trade",
    )

    assert decision.action == "reply"
    assert decision.reason == "refuse_trade_advice"
    assert "cannot tell you what to trade" in decision.reply


def test_representative_routes_channel_questions() -> None:
    message = {
        "id": "102",
        "content": "<@bot_1> where do I post a setup idea?",
        "author": {"id": "user_1", "bot": False},
        "mentions": [{"id": "bot_1"}],
    }

    decision = rep.classify_message(
        message,
        bot_user_id="bot_1",
        channel_name="questions",
        allowed_channel_ids={"chan_questions"},
        channel_id="chan_questions",
    )

    assert decision.action == "reply"
    assert decision.reason == "route_trade_ideas"
    assert "#trade-ideas" in decision.reply
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests\unit\test_coinfox_discord_representative.py -q
```

Expected: import failure because `foxclaw.adapters.discord.representative` does not exist.

- [ ] **Step 3: Implement the minimal policy**

Create `foxclaw/adapters/discord/representative.py` with:

```python
"""Mention-only CoinFox Discord representative bot helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RepresentativeDecision:
    action: str
    reason: str
    reply: str | None = None


TRADE_ADVICE_TERMS = (
    "should i buy",
    "should i sell",
    "buy now",
    "sell now",
    "enter",
    "exit",
    "leverage",
    "position size",
)

PRIVATE_HISTORY_TERMS = (
    "founder vault",
    "reset staging",
    "archive",
    "old signals",
    "private history",
    "bot log",
    "parser log",
)

CHANNEL_ROUTE_TERMS = ("where do i post", "setup idea", "trade idea", "which channel")

IDENTITY_REPLY = (
    "I am the CoinFox bot. I can explain the server, route questions, and keep "
    "the risk line clear. I cannot give financial advice or tell anyone what to trade."
)

TRADE_ADVICE_REFUSAL = (
    "I cannot tell you what to trade. I can help frame the idea, risk, "
    "invalidation, and where to discuss it. For setups, use #trade-ideas and "
    "label uncertainty clearly."
)

PRIVATE_HISTORY_REFUSAL = (
    "I cannot discuss private archives, Founder Vault, Reset Staging, or old "
    "server history. I can help with the public CoinFox channels and public-safe "
    "rules."
)

TRADE_IDEAS_ROUTE = (
    "Use #trade-ideas for structured setups. Include the idea, timeframe, risk, "
    "invalidation point, and what would change your mind."
)


def classify_message(
    message: dict[str, Any],
    *,
    bot_user_id: str,
    channel_name: str,
    allowed_channel_ids: set[str],
    channel_id: str,
) -> RepresentativeDecision:
    if channel_id not in allowed_channel_ids:
        return RepresentativeDecision("ignore", "channel_not_allowed")
    author = message.get("author") if isinstance(message.get("author"), dict) else {}
    if author.get("bot"):
        return RepresentativeDecision("ignore", "bot_author")
    if not _mentions_bot(message, bot_user_id):
        return RepresentativeDecision("ignore", "not_mentioned")

    content = str(message.get("content") or "").lower()
    if _contains_any(content, PRIVATE_HISTORY_TERMS):
        return RepresentativeDecision("reply", "refuse_private_history", PRIVATE_HISTORY_REFUSAL)
    if _contains_any(content, TRADE_ADVICE_TERMS):
        return RepresentativeDecision("reply", "refuse_trade_advice", TRADE_ADVICE_REFUSAL)
    if _contains_any(content, CHANNEL_ROUTE_TERMS):
        return RepresentativeDecision("reply", "route_trade_ideas", TRADE_IDEAS_ROUTE)
    return RepresentativeDecision("reply", "identity", IDENTITY_REPLY)


def _mentions_bot(message: dict[str, Any], bot_user_id: str) -> bool:
    return any(str(mention.get("id") or "") == bot_user_id for mention in message.get("mentions") or [])


def _contains_any(content: str, terms: tuple[str, ...]) -> bool:
    return any(term in content for term in terms)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests\unit\test_coinfox_discord_representative.py -q
```

Expected: all representative policy tests pass.

- [ ] **Step 5: Commit**

Run:

```powershell
git add foxclaw/adapters/discord/representative.py tests/unit/test_coinfox_discord_representative.py
git commit -m "feat: add CoinFox representative policy"
```

## Task 2: State Store And One-Cycle Dry Run

**Files:**
- Modify: `foxclaw/adapters/discord/representative.py`
- Test: `tests/unit/test_coinfox_discord_representative.py`

- [ ] **Step 1: Write failing dry-run tests**

Append tests:

```python
from pathlib import Path


class FakeRepresentativeClient:
    def __init__(self) -> None:
        self.replies: list[tuple[str, str, str]] = []
        self.messages = {
            "chan_general": [
                {
                    "id": "200",
                    "content": "<@bot_1> what is CoinFox?",
                    "author": {"id": "user_1", "bot": False},
                    "mentions": [{"id": "bot_1"}],
                }
            ]
        }

    def channel_messages(self, channel_id: str, *, after: str | None = None, limit: int = 50):
        return list(self.messages.get(channel_id, []))

    def create_message(self, channel_id: str, content: str, *, message_reference: str):
        self.replies.append((channel_id, content, message_reference))
        return {"id": "reply_1", "content": content}


def test_run_once_dry_run_does_not_send_reply(tmp_path: Path) -> None:
    client = FakeRepresentativeClient()

    result = rep.run_once(
        client,
        bot_user_id="bot_1",
        channels={"chan_general": "general"},
        state_path=tmp_path / "state.json",
        send=False,
    )

    assert result["processed"] == 1
    assert result["would_reply"] == 1
    assert result["sent"] == 0
    assert client.replies == []


def test_run_once_send_posts_reply_and_updates_state(tmp_path: Path) -> None:
    client = FakeRepresentativeClient()
    state_path = tmp_path / "state.json"

    result = rep.run_once(
        client,
        bot_user_id="bot_1",
        channels={"chan_general": "general"},
        state_path=state_path,
        send=True,
    )

    assert result["sent"] == 1
    assert client.replies[0][0] == "chan_general"
    assert client.replies[0][2] == "200"
    assert rep.load_state(state_path)["chan_general"] == "200"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests\unit\test_coinfox_discord_representative.py::test_run_once_dry_run_does_not_send_reply tests\unit\test_coinfox_discord_representative.py::test_run_once_send_posts_reply_and_updates_state -q
```

Expected: failure because `run_once` and state helpers are missing.

- [ ] **Step 3: Implement state and run_once**

Add to `representative.py`:

```python
import json
from pathlib import Path


def load_state(path: str | Path) -> dict[str, str]:
    state_path = Path(path)
    if not state_path.exists():
        return {}
    return {str(key): str(value) for key, value in json.loads(state_path.read_text(encoding="utf-8")).items()}


def save_state(path: str | Path, state: dict[str, str]) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_once(
    client: Any,
    *,
    bot_user_id: str,
    channels: dict[str, str],
    state_path: str | Path,
    send: bool = False,
) -> dict[str, int]:
    state = load_state(state_path)
    summary = {"processed": 0, "would_reply": 0, "sent": 0, "ignored": 0}
    allowed_channel_ids = set(channels)
    for channel_id, channel_name in channels.items():
        after = state.get(channel_id)
        messages = client.channel_messages(channel_id, after=after, limit=50)
        for message in sorted(messages, key=lambda item: int(str(item.get("id") or "0"))):
            message_id = str(message.get("id") or "")
            if not message_id:
                continue
            decision = classify_message(
                message,
                bot_user_id=bot_user_id,
                channel_name=channel_name,
                allowed_channel_ids=allowed_channel_ids,
                channel_id=channel_id,
            )
            summary["processed"] += 1
            if decision.action == "reply" and decision.reply:
                summary["would_reply"] += 1
                if send:
                    client.create_message(channel_id, decision.reply, message_reference=message_id)
                    summary["sent"] += 1
            else:
                summary["ignored"] += 1
            state[channel_id] = message_id
    save_state(state_path, state)
    return summary
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests\unit\test_coinfox_discord_representative.py -q
```

Expected: all representative tests pass.

- [ ] **Step 5: Commit**

Run:

```powershell
git add foxclaw/adapters/discord/representative.py tests/unit/test_coinfox_discord_representative.py
git commit -m "feat: add representative dry-run cycle"
```

## Task 3: Discord REST Client And CLI

**Files:**
- Modify: `foxclaw/adapters/discord/representative.py`
- Create: `tools/coinfox_discord_rep.py`
- Test: `tests/unit/test_coinfox_discord_representative.py`

- [ ] **Step 1: Write failing CLI/client tests**

Append tests:

```python
def test_default_state_path_is_outside_repo_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    path = rep.default_state_path()

    assert path == tmp_path / ".coinfox" / "discord_rep_state.json"


def test_parse_public_channels_requires_name_and_id(tmp_path: Path) -> None:
    config = tmp_path / "channels.json"
    config.write_text(
        '{"channels":[{"id":"chan_general","name":"general"},{"id":"chan_help","name":"help"}]}',
        encoding="utf-8",
    )

    assert rep.load_channel_config(config) == {
        "chan_general": "general",
        "chan_help": "help",
    }
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests\unit\test_coinfox_discord_representative.py::test_default_state_path_is_outside_repo_home tests\unit\test_coinfox_discord_representative.py::test_parse_public_channels_requires_name_and_id -q
```

Expected: failure because config/state helpers are missing.

- [ ] **Step 3: Implement config helpers and REST client**

Add to `representative.py`:

```python
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from foxclaw.adapters.discord.archive import API_BASE, DiscordAPIError, bot_token_from_env


@dataclass(frozen=True)
class DiscordRepresentativeClient:
    token: str
    base_url: str = API_BASE
    user_agent: str = "coinfox-discord-rep/0.1"

    def me(self) -> dict[str, Any]:
        return _ensure_dict(self.request_json("GET", "/users/@me"))

    def channel_messages(
        self, channel_id: str, *, after: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        params = {"limit": str(max(1, min(limit, 100)))}
        if after:
            params["after"] = after
        return _ensure_list_of_dicts(
            self.request_json("GET", f"/channels/{channel_id}/messages", params=params)
        )

    def create_message(
        self, channel_id: str, content: str, *, message_reference: str
    ) -> dict[str, Any]:
        payload = {"content": content, "message_reference": {"message_id": message_reference}}
        return _ensure_dict(self.request_json("POST", f"/channels/{channel_id}/messages", payload=payload))

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._url(path, params=params),
            data=data,
            method=method,
            headers={
                "Authorization": f"Bot {self.token}",
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                body = response.read().decode("utf-8")
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise DiscordAPIError(f"discord request failed: HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise DiscordAPIError(f"discord request failed: {exc.reason}") from exc

    def _url(self, path: str, *, params: dict[str, str] | None = None) -> str:
        url = self.base_url.rstrip("/") + "/" + path.lstrip("/")
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url


def client_from_env() -> DiscordRepresentativeClient:
    return DiscordRepresentativeClient(token=bot_token_from_env())


def default_state_path() -> Path:
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or str(Path.home()))
    return home / ".coinfox" / "discord_rep_state.json"


def load_channel_config(path: str | Path) -> dict[str, str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    channels: dict[str, str] = {}
    for item in payload.get("channels") or []:
        channel_id = str(item.get("id") or "")
        name = str(item.get("name") or "")
        if not channel_id or not name:
            raise ValueError("each channel config item requires id and name")
        channels[channel_id] = name
    return channels


def _ensure_dict(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    raise DiscordAPIError("discord response was not an object")


def _ensure_list_of_dicts(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    raise DiscordAPIError("discord response was not a list of objects")
```

- [ ] **Step 4: Add CLI**

Create `tools/coinfox_discord_rep.py`:

```python
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
```

- [ ] **Step 5: Run representative tests and compile check**

Run:

```powershell
python -m pytest tests\unit\test_coinfox_discord_representative.py -q
python -m py_compile foxclaw\adapters\discord\representative.py tools\coinfox_discord_rep.py
```

Expected: tests pass and compile exits 0.

- [ ] **Step 6: Commit**

Run:

```powershell
git add foxclaw/adapters/discord/representative.py tools/coinfox_discord_rep.py tests/unit/test_coinfox_discord_representative.py
git commit -m "feat: add CoinFox representative CLI"
```

## Task 4: Public Channel Config And Operator Docs

**Files:**
- Create: `config/coinfox_discord_public_channels.example.json`
- Modify: `docs/CoinFox_Discord_Reset_Operator_Checklist.md`

- [ ] **Step 1: Create example public channel config**

Create `config/coinfox_discord_public_channels.example.json`:

```json
{
  "channels": [
    {"id": "REPLACE_WITH_WELCOME_CHANNEL_ID", "name": "welcome"},
    {"id": "REPLACE_WITH_RULES_CHANNEL_ID", "name": "rules"},
    {"id": "REPLACE_WITH_ANNOUNCEMENTS_CHANNEL_ID", "name": "announcements"},
    {"id": "REPLACE_WITH_GENERAL_CHANNEL_ID", "name": "general"},
    {"id": "REPLACE_WITH_PRODUCT_UPDATES_CHANNEL_ID", "name": "product-updates"},
    {"id": "REPLACE_WITH_MARKET_TALK_CHANNEL_ID", "name": "market-talk"},
    {"id": "REPLACE_WITH_TRADE_IDEAS_CHANNEL_ID", "name": "trade-ideas"},
    {"id": "REPLACE_WITH_RISK_DESK_CHANNEL_ID", "name": "risk-desk"},
    {"id": "REPLACE_WITH_GOOD_SIGNAL_BAD_TRADE_CHANNEL_ID", "name": "good-signal-bad-trade"},
    {"id": "REPLACE_WITH_POSTMORTEMS_CHANNEL_ID", "name": "postmortems"},
    {"id": "REPLACE_WITH_PUBLIC_INTEL_CHANNEL_ID", "name": "public-intel"},
    {"id": "REPLACE_WITH_NO_EDGE_REJECTS_CHANNEL_ID", "name": "no-edge-rejects"},
    {"id": "REPLACE_WITH_PAPER_NOTES_CHANNEL_ID", "name": "paper-notes"},
    {"id": "REPLACE_WITH_TESTING_GROUND_CHANNEL_ID", "name": "testing-ground"},
    {"id": "REPLACE_WITH_FEEDBACK_AND_IDEAS_CHANNEL_ID", "name": "feedback-and-ideas"},
    {"id": "REPLACE_WITH_COMMUNITY_EVENTS_CHANNEL_ID", "name": "community-events"},
    {"id": "REPLACE_WITH_BEGINNER_QUESTIONS_CHANNEL_ID", "name": "beginner-questions"},
    {"id": "REPLACE_WITH_RISK_MANAGEMENT_CHANNEL_ID", "name": "risk-management"},
    {"id": "REPLACE_WITH_BEFORE_YOU_CLICK_CHANNEL_ID", "name": "before-you-click"},
    {"id": "REPLACE_WITH_HELP_DESK_CHANNEL_ID", "name": "help-desk"}
  ]
}
```

- [ ] **Step 2: Add checklist operator notes**

Append a section to `docs/CoinFox_Discord_Reset_Operator_Checklist.md`:

```markdown
## Optional Mention-Only Representative Bot

`tools/coinfox_discord_rep.py` runs the CoinFox bot as a public-channel
representative. It is mention-only and dry-run by default.

Safety boundary:

- only channels listed in the JSON allowlist are polled;
- no private archive files are read;
- no Founder Vault, Reset Staging, raw feed, parser log, bot log, or old signal
  channel should appear in the allowlist;
- live posting requires `--send`;
- no trade advice, trade execution, signal parsing, moderation automation, or
  public invite creation.

Dry run:

```powershell
python tools\coinfox_discord_rep.py --channels-config config\coinfox_discord_public_channels.local.json
```

Live send:

```powershell
python tools\coinfox_discord_rep.py --channels-config config\coinfox_discord_public_channels.local.json --send
```

Keep `config\coinfox_discord_public_channels.local.json` out of git if it
contains live Discord channel IDs.
```

- [ ] **Step 3: Run docs and tests verification**

Run:

```powershell
python -m pytest tests\unit\test_coinfox_discord_representative.py -q
git diff --check
```

Expected: tests pass and diff check exits 0.

- [ ] **Step 4: Commit**

Run:

```powershell
git add config/coinfox_discord_public_channels.example.json docs/CoinFox_Discord_Reset_Operator_Checklist.md
git commit -m "docs: document CoinFox representative bot operations"
```

## Task 5: Final Verification And Dry-Run Preparation

**Files:**
- No production file changes unless verification finds a defect.

- [ ] **Step 1: Run full tests**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass with the existing skipped-test count unchanged or explained.

- [ ] **Step 2: Run compile check**

Run:

```powershell
python -m py_compile foxclaw\adapters\discord\representative.py tools\coinfox_discord_rep.py
```

Expected: exit 0.

- [ ] **Step 3: Run secret scan over new files**

Run:

```powershell
rg -n "Bot [A-Za-z0-9_\\.-]+|mfa\\.|COINFOX_DISCORD_BOT_TOKEN\\s*=|USER_TOKEN\\s*=" foxclaw\adapters\discord\representative.py tools\coinfox_discord_rep.py tests\unit\test_coinfox_discord_representative.py docs config -S
```

Expected: no real token values; documentation references to environment variable names are acceptable.

- [ ] **Step 4: Run git status**

Run:

```powershell
git status --short
```

Expected: clean after commits.

## Self-Review

- Spec coverage: mention-only gating is Task 1; public allowlist is Tasks 1 and 3; deterministic knowledge/refusals are Task 1; dry-run and explicit send are Tasks 2 and 3; no private archive access is enforced by config and documented in Task 4; tests are included in every implementation task.
- Placeholder scan: the plan uses concrete filenames, commands, and code snippets. `REPLACE_WITH_*` appears only in an example config intended not to be live.
- Type consistency: `RepresentativeDecision`, `classify_message`, `run_once`, `load_state`, `save_state`, `default_state_path`, `load_channel_config`, and `DiscordRepresentativeClient` are consistently named across tasks.
