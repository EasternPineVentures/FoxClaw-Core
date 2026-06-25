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

    def patch_guild(self, guild_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return _ensure_dict(self.request_json("PATCH", f"/guilds/{guild_id}", payload))

    def create_guild_channel(self, guild_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return _ensure_dict(self.request_json("POST", f"/guilds/{guild_id}/channels", payload))

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
    missing: list[str] = []
    if not has_manage_guild:
        missing.append("MANAGE_GUILD")
    if not has_manage_channels:
        missing.append("MANAGE_CHANNELS")
    return {
        "has_manage_guild": has_manage_guild,
        "has_manage_channels": has_manage_channels,
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
