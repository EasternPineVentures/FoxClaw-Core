"""Explicit live Discord reset helpers for the CoinFox server.

Unlike the archive helper, this module can mutate Discord state. Its public
operations are intentionally narrow: revoke invites and create the documented
CoinFox reset structure. It does not delete channels.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from foxclaw.adapters.discord.archive import (
    API_BASE,
    DiscordAPIError,
    bot_token_from_env,
)

CHANNEL_TYPE_TEXT = 0
CHANNEL_TYPE_CATEGORY = 4
OVERWRITE_TYPE_ROLE = 0

PERMISSION_VIEW_CHANNEL = 1 << 10
PERMISSION_MANAGE_CHANNELS = 1 << 4
PERMISSION_MANAGE_GUILD = 1 << 5
PERMISSION_SEND_MESSAGES = 1 << 11
PERMISSION_MANAGE_MESSAGES = 1 << 13
PERMISSION_READ_MESSAGE_HISTORY = 1 << 16

PRIVATE_LAYOUT = {
    "FOUNDER VAULT": [
        "founder-footnotes",
        "archived-decisions",
        "signal-history-index",
    ],
    "RESET STAGING": [
        "review-delete",
        "review-lock",
        "review-archive-only",
        "permissions-test",
    ],
}

PUBLIC_LAYOUT = {
    "START HERE": ["welcome", "rules", "announcements", "roles"],
    "COINFOX": ["general", "market-talk", "trade-ideas", "questions", "wins-and-lessons"],
    "FOXCLAW IDEAS": [
        "public-intelligence",
        "paper-only-notes",
        "no-edge-rejects",
        "foxclaw-postmortems",
    ],
    "LEARN": [
        "risk-management",
        "good-signal-bad-trade",
        "plan-before-entry",
        "beginner-questions",
    ],
    "SUPPORT": ["help", "reports"],
}

PUBLIC_CATEGORY_NAMES = set(PUBLIC_LAYOUT)
PRIVATE_CATEGORY_NAMES = set(PRIVATE_LAYOUT)
COINFOX_CATEGORY_NAMES = PUBLIC_CATEGORY_NAMES | PRIVATE_CATEGORY_NAMES

FIRST_PINNED_POSTS = [
    {
        "category": "START HERE",
        "channel": "welcome",
        "marker": "CoinFox Launch Note: Welcome",
        "content": """**CoinFox Launch Note: Welcome**

Welcome to CoinFox.

CoinFox is a social trading and prediction discussion community built around structured ideas, receipts, risk discipline, and learning from outcomes.

Nothing here is financial advice. No post is a command to trade. A good signal is not automatically a good trade.

FoxClaw may generate public-safe ideas, paper-only notes, or postmortems here. These are for research and learning. Risk labels matter.

The Market Remembers. Receipts over hype.""",
    },
    {
        "category": "START HERE",
        "channel": "rules",
        "marker": "CoinFox Launch Note: Rules",
        "content": """**CoinFox Launch Note: Rules**

1. Keep public discussion respectful and useful.
2. Do not post private keys, account credentials, personal documents, or sensitive screenshots.
3. Label speculation clearly.
4. No spam, pump campaigns, impersonation, or paid promotion without disclosure.
5. Respect risk. Challenge ideas with reasoning, not personal attacks.
6. Founder Vault and archived material stay private unless founder-approved and redacted.""",
    },
    {
        "category": "START HERE",
        "channel": "rules",
        "marker": "CoinFox Launch Note: Risk Disclaimer",
        "content": """**CoinFox Launch Note: Risk Disclaimer**

CoinFox is for education, research, journaling, and public market discussion.

Nothing in this Discord is financial, investment, tax, legal, or trading advice. Markets can move fast, losses are possible, and every person is responsible for their own decisions.

Treat every idea as incomplete until you have your own plan, invalidation level, position sizing, and risk limit.""",
    },
    {
        "category": "COINFOX",
        "channel": "trade-ideas",
        "marker": "CoinFox Launch Note: Signals Are Not Trades",
        "content": """**CoinFox Launch Note: Signals Are Not Trades**

A signal is an idea, not an order.

A trade requires context: account risk, entry plan, invalidation, timeframe, liquidity, and whether the idea still makes sense when price changes.

Post ideas clearly. Separate observation from conviction. If the plan changes, say so.""",
    },
    {
        "category": "COINFOX",
        "channel": "trade-ideas",
        "marker": "CoinFox Launch Note: How To Use Trade Ideas",
        "content": """**CoinFox Launch Note: How To Use Trade Ideas**

Use trade-ideas for structured setups and paper-trade discussion.

Helpful posts include: ticker or asset, timeframe, thesis, invalidation, risk notes, what would prove the idea wrong, and whether it is live, watched, or paper-only.

Do not treat another person's idea as permission to skip your own plan.""",
    },
    {
        "category": "FOXCLAW IDEAS",
        "channel": "public-intelligence",
        "marker": "CoinFox Launch Note: FoxClaw Public Intelligence",
        "content": """**CoinFox Launch Note: FoxClaw Public Intelligence**

FoxClaw public intelligence means public-safe market observations, research notes, risk labels, and postmortems that can be discussed without exposing private founder material.

It is not a private signal feed. It is not a trading command system. It is a receipt trail for learning what the market did, what the model saw, and what still needs review.""",
    },
    {
        "category": "SUPPORT",
        "channel": "help",
        "marker": "CoinFox Launch Note: Help",
        "content": """**CoinFox Launch Note: Help**

Use this channel for access questions, confusing server behavior, broken links, or safety concerns.

Do not post passwords, private keys, account numbers, or sensitive screenshots. If something needs founder review, say what happened and keep private details out of public chat.""",
    },
]


@dataclass(frozen=True)
class DiscordResetClient:
    token: str
    base_url: str = API_BASE
    user_agent: str = "coinfox-discord-reset/0.1"

    def me(self) -> dict[str, Any]:
        return _ensure_dict(self.request_json("GET", "/users/@me"))

    def guild_member(self, guild_id: str, user_id: str) -> dict[str, Any]:
        return _ensure_dict(self.request_json("GET", f"/guilds/{guild_id}/members/{user_id}"))

    def guild_roles(self, guild_id: str) -> list[dict[str, Any]]:
        return _ensure_list_of_dicts(self.request_json("GET", f"/guilds/{guild_id}/roles"))

    def guild_channels(self, guild_id: str) -> list[dict[str, Any]]:
        return _ensure_list_of_dicts(self.request_json("GET", f"/guilds/{guild_id}/channels"))

    def guild_invites(self, guild_id: str) -> list[dict[str, Any]]:
        return _ensure_list_of_dicts(self.request_json("GET", f"/guilds/{guild_id}/invites"))

    def channel_pins(self, channel_id: str) -> list[dict[str, Any]]:
        return _ensure_list_of_dicts(self.request_json("GET", f"/channels/{channel_id}/pins"))

    def patch_guild(self, guild_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return _ensure_dict(self.request_json("PATCH", f"/guilds/{guild_id}", payload))

    def create_guild_channel(self, guild_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return _ensure_dict(self.request_json("POST", f"/guilds/{guild_id}/channels", payload))

    def create_message(self, channel_id: str, content: str) -> dict[str, Any]:
        return _ensure_dict(
            self.request_json("POST", f"/channels/{channel_id}/messages", {"content": content})
        )

    def pin_message(self, channel_id: str, message_id: str) -> dict[str, Any]:
        self.request_json("PUT", f"/channels/{channel_id}/pins/{message_id}")
        return {"channel_id": channel_id, "message_id": message_id}

    def patch_channel(self, channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return _ensure_dict(self.request_json("PATCH", f"/channels/{channel_id}", payload))

    def delete_invite(self, code: str) -> dict[str, Any]:
        result = self.request_json("DELETE", f"/invites/{urllib.parse.quote(code)}")
        return _ensure_dict(result or {"code": code})

    def request_json(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self._url(path),
            data=data,
            method=method,
            headers={
                "Authorization": f"Bot {self.token}",
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        for attempt in range(2):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                    body = response.read().decode("utf-8")
                    return json.loads(body) if body else None
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code == 429 and attempt == 0:
                    time.sleep(min(_retry_after_seconds(body), 5.0))
                    continue
                raise DiscordAPIError(_discord_error_message(exc.code, body)) from exc
            except urllib.error.URLError as exc:
                raise DiscordAPIError(f"discord request failed: {exc.reason}") from exc
        raise DiscordAPIError("discord request failed after retry")

    def _url(self, path: str) -> str:
        return self.base_url.rstrip("/") + "/" + path.lstrip("/")


def client_from_env() -> DiscordResetClient:
    return DiscordResetClient(token=bot_token_from_env())


def revoke_all_invites(client: Any, guild_id: str) -> dict[str, Any]:
    revoked: list[str] = []
    for invite in client.guild_invites(guild_id):
        code = str(invite.get("code") or "")
        if not code:
            continue
        client.delete_invite(code)
        revoked.append(code)
    return {"revoked": revoked, "count": len(revoked)}


def rename_guild(client: Any, guild_id: str, name: str) -> dict[str, Any]:
    guild = client.patch_guild(guild_id, {"name": name})
    return {"guild_id": str(guild.get("id") or guild_id), "name": str(guild.get("name") or name)}


def ensure_reset_structure(client: Any, guild_id: str) -> dict[str, Any]:
    channels = client.guild_channels(guild_id)
    created_categories: list[str] = []
    created_channels: list[str] = []
    updated_categories: list[str] = []

    for category_name, child_names in {**PRIVATE_LAYOUT, **PUBLIC_LAYOUT}.items():
        private = category_name in PRIVATE_LAYOUT
        category = _find_category(channels, category_name)
        overwrites = _private_category_overwrites(guild_id) if private else []
        if category is None:
            payload: dict[str, Any] = {"name": category_name, "type": CHANNEL_TYPE_CATEGORY}
            if overwrites:
                payload["permission_overwrites"] = overwrites
            category = client.create_guild_channel(guild_id, payload)
            channels.append(category)
            created_categories.append(category_name)
        elif private:
            patched_overwrites = _upsert_everyone_private_overwrite(
                category.get("permission_overwrites") or [], guild_id
            )
            if patched_overwrites != (category.get("permission_overwrites") or []):
                category = client.patch_channel(
                    str(category["id"]), {"permission_overwrites": patched_overwrites}
                )
                updated_categories.append(category_name)

        parent_id = str(category["id"])
        for channel_name in child_names:
            if _find_text_channel(channels, channel_name, parent_id) is not None:
                continue
            channel = client.create_guild_channel(
                guild_id,
                {
                    "name": channel_name,
                    "type": CHANNEL_TYPE_TEXT,
                    "parent_id": parent_id,
                },
            )
            channels.append(channel)
            created_channels.append(channel_name)

    return {
        "created_categories": created_categories,
        "created_channels": created_channels,
        "updated_categories": updated_categories,
    }


def hide_legacy_surface(client: Any, guild_id: str) -> dict[str, Any]:
    channels = client.guild_channels(guild_id)
    categories_by_id = {
        str(channel.get("id") or ""): channel
        for channel in channels
        if channel.get("type") == CHANNEL_TYPE_CATEGORY
    }
    hidden: list[str] = []
    skipped: list[str] = []
    failures: list[dict[str, str]] = []
    for channel in channels:
        channel_name = str(channel.get("name") or channel.get("id") or "")
        if not _should_hide_for_public(channel, categories_by_id):
            skipped.append(channel_name)
            continue
        patched_overwrites = _upsert_everyone_deny_view(
            channel.get("permission_overwrites") or [], guild_id
        )
        if patched_overwrites == (channel.get("permission_overwrites") or []):
            skipped.append(channel_name)
            continue
        channel_id = str(channel["id"])
        try:
            client.patch_channel(channel_id, {"permission_overwrites": patched_overwrites})
        except DiscordAPIError as exc:
            failures.append({"channel": channel_name, "channel_id": channel_id, "error": str(exc)})
            continue
        hidden.append(channel_name)
    return {
        "hidden": hidden,
        "hidden_count": len(hidden),
        "skipped": skipped,
        "failures": failures,
        "failure_count": len(failures),
    }


def seed_first_pinned_posts(client: Any, guild_id: str) -> dict[str, Any]:
    channels = client.guild_channels(guild_id)
    posted: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    missing_channels: list[dict[str, str]] = []

    for post in FIRST_PINNED_POSTS:
        category_name = str(post["category"])
        channel_name = str(post["channel"])
        marker = str(post["marker"])
        channel = _find_public_text_channel(channels, category_name, channel_name)
        if channel is None:
            missing_channels.append({"category": category_name, "channel": channel_name})
            continue

        channel_id = str(channel["id"])
        if _channel_has_pin_marker(client.channel_pins(channel_id), marker):
            skipped.append({"channel": channel_name, "marker": marker})
            continue

        message = client.create_message(channel_id, str(post["content"]))
        message_id = str(message["id"])
        client.pin_message(channel_id, message_id)
        posted.append({"channel": channel_name, "message_id": message_id, "marker": marker})

    return {
        "posted": posted,
        "posted_count": len(posted),
        "skipped": skipped,
        "skipped_count": len(skipped),
        "missing_channels": missing_channels,
        "missing_channel_count": len(missing_channels),
    }


def permission_report(
    roles: list[dict[str, Any]], member_role_ids: list[str], guild_id: str
) -> dict[str, Any]:
    permissions = 0
    role_ids = {guild_id, *member_role_ids}
    for role in roles:
        if str(role.get("id") or "") not in role_ids:
            continue
        permissions |= int(str(role.get("permissions") or "0"))
    has_manage_guild = bool(permissions & PERMISSION_MANAGE_GUILD)
    has_manage_channels = bool(permissions & PERMISSION_MANAGE_CHANNELS)
    has_send_messages = bool(permissions & PERMISSION_SEND_MESSAGES)
    has_manage_messages = bool(permissions & PERMISSION_MANAGE_MESSAGES)
    has_read_message_history = bool(permissions & PERMISSION_READ_MESSAGE_HISTORY)
    missing: list[str] = []
    if not has_manage_guild:
        missing.append("MANAGE_GUILD")
    if not has_manage_channels:
        missing.append("MANAGE_CHANNELS")
    if not has_send_messages:
        missing.append("SEND_MESSAGES")
    if not has_manage_messages:
        missing.append("MANAGE_MESSAGES")
    if not has_read_message_history:
        missing.append("READ_MESSAGE_HISTORY")
    return {
        "has_manage_guild": has_manage_guild,
        "has_manage_channels": has_manage_channels,
        "has_send_messages": has_send_messages,
        "has_manage_messages": has_manage_messages,
        "has_read_message_history": has_read_message_history,
        "missing": missing,
        "permissions": str(permissions),
    }


def live_permission_report(client: DiscordResetClient, guild_id: str) -> dict[str, Any]:
    me = client.me()
    member = client.guild_member(guild_id, str(me["id"]))
    roles = client.guild_roles(guild_id)
    report = permission_report(roles, [str(role_id) for role_id in member.get("roles", [])], guild_id)
    report["bot_user_id"] = str(me["id"])
    report["bot_username"] = str(me.get("username") or "")
    report["role_ids"] = [str(role_id) for role_id in member.get("roles", [])]
    return report


def _find_category(channels: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    return next(
        (
            channel
            for channel in channels
            if channel.get("type") == CHANNEL_TYPE_CATEGORY and channel.get("name") == name
        ),
        None,
    )


def _find_text_channel(
    channels: list[dict[str, Any]], name: str, parent_id: str
) -> dict[str, Any] | None:
    return next(
        (
            channel
            for channel in channels
            if channel.get("type") == CHANNEL_TYPE_TEXT
            and channel.get("name") == name
            and str(channel.get("parent_id") or "") == parent_id
        ),
        None,
    )


def _find_public_text_channel(
    channels: list[dict[str, Any]], category_name: str, channel_name: str
) -> dict[str, Any] | None:
    category = _find_category(channels, category_name)
    if category is None:
        return None
    return _find_text_channel(channels, channel_name, str(category["id"]))


def _channel_has_pin_marker(pins: list[dict[str, Any]], marker: str) -> bool:
    return any(marker in str(pin.get("content") or "") for pin in pins)


def _private_category_overwrites(guild_id: str) -> list[dict[str, str | int]]:
    return [
        {
            "id": guild_id,
            "type": OVERWRITE_TYPE_ROLE,
            "allow": "0",
            "deny": str(PERMISSION_VIEW_CHANNEL),
        }
    ]


def _should_hide_for_public(
    channel: dict[str, Any], categories_by_id: dict[str, dict[str, Any]]
) -> bool:
    channel_type = channel.get("type")
    if channel_type == CHANNEL_TYPE_CATEGORY:
        return str(channel.get("name") or "") not in COINFOX_CATEGORY_NAMES
    parent_id = str(channel.get("parent_id") or "")
    parent = categories_by_id.get(parent_id)
    parent_name = str(parent.get("name") or "") if parent else ""
    return parent_name not in COINFOX_CATEGORY_NAMES


def _upsert_everyone_deny_view(
    overwrites: list[dict[str, Any]], guild_id: str
) -> list[dict[str, str | int]]:
    result: list[dict[str, str | int]] = []
    replaced = False
    for overwrite in overwrites:
        if str(overwrite.get("id") or "") == guild_id and overwrite.get("type") == OVERWRITE_TYPE_ROLE:
            allow = int(str(overwrite.get("allow") or "0")) & ~PERMISSION_VIEW_CHANNEL
            deny = int(str(overwrite.get("deny") or "0")) | PERMISSION_VIEW_CHANNEL
            result.append(
                {
                    "id": guild_id,
                    "type": OVERWRITE_TYPE_ROLE,
                    "allow": str(allow),
                    "deny": str(deny),
                }
            )
            replaced = True
        else:
            result.append(
                {
                    "id": str(overwrite.get("id") or ""),
                    "type": int(overwrite.get("type") or 0),
                    "allow": str(overwrite.get("allow") or "0"),
                    "deny": str(overwrite.get("deny") or "0"),
                }
            )
    if not replaced:
        result.append(
            {
                "id": guild_id,
                "type": OVERWRITE_TYPE_ROLE,
                "allow": "0",
                "deny": str(PERMISSION_VIEW_CHANNEL),
            }
        )
    return result


def _upsert_everyone_private_overwrite(
    overwrites: list[dict[str, Any]], guild_id: str
) -> list[dict[str, str | int]]:
    replacement = _private_category_overwrites(guild_id)[0]
    result: list[dict[str, str | int]] = []
    replaced = False
    for overwrite in overwrites:
        if str(overwrite.get("id") or "") == guild_id and overwrite.get("type") == OVERWRITE_TYPE_ROLE:
            result.append(replacement)
            replaced = True
        else:
            result.append(
                {
                    "id": str(overwrite.get("id") or ""),
                    "type": int(overwrite.get("type") or 0),
                    "allow": str(overwrite.get("allow") or "0"),
                    "deny": str(overwrite.get("deny") or "0"),
                }
            )
    if not replaced:
        result.append(replacement)
    return result


def _retry_after_seconds(body: str) -> float:
    try:
        payload = json.loads(body)
        return float(payload.get("retry_after") or 1.0)
    except (TypeError, ValueError, json.JSONDecodeError):
        return 1.0


def _discord_error_message(status: int, body: str) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = {}
    message = payload.get("message") if isinstance(payload, dict) else ""
    code = payload.get("code") if isinstance(payload, dict) else ""
    suffix = f" Discord code {code}" if code else ""
    return f"discord request failed: HTTP {status}{suffix}: {message or body}"


def _ensure_dict(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    raise DiscordAPIError("discord response was not an object")


def _ensure_list_of_dicts(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    raise DiscordAPIError("discord response was not a list of objects")
