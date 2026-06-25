"""Mention-only CoinFox Discord representative bot helpers."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foxclaw.adapters.discord.archive import API_BASE, DiscordAPIError, bot_token_from_env


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
        return _ensure_dict(
            self.request_json("POST", f"/channels/{channel_id}/messages", payload=payload)
        )

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


def load_state(path: str | Path) -> dict[str, str]:
    state_path = Path(path)
    if not state_path.exists():
        return {}
    return {
        str(key): str(value)
        for key, value in json.loads(state_path.read_text(encoding="utf-8")).items()
    }


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


def _mentions_bot(message: dict[str, Any], bot_user_id: str) -> bool:
    return any(
        str(mention.get("id") or "") == bot_user_id for mention in message.get("mentions") or []
    )


def _contains_any(content: str, terms: tuple[str, ...]) -> bool:
    return any(term in content for term in terms)


def _ensure_dict(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    raise DiscordAPIError("discord response was not an object")


def _ensure_list_of_dicts(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    raise DiscordAPIError("discord response was not a list of objects")
