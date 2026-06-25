"""Read-only CoinFox Discord archive helpers.

This module is intentionally bot-token only. It can read Discord metadata and
message history through the official REST API, then write local private archive
artifacts. It never deletes, moves, locks, or creates Discord resources.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

API_BASE = "https://discord.com/api/v10"
BOT_TOKEN_ENV = "COINFOX_DISCORD_BOT_TOKEN"
LEGACY_USER_TOKEN_ENV = "USER_TOKEN"

TRACKER_HEADER = (
    "channel_name",
    "category",
    "archive_status",
    "pins_saved",
    "attachments_saved",
    "decision",
    "public_after_reset",
    "notes",
)

EXPORT_BUCKETS = {
    "founder-notes",
    "signal-history",
    "important-decisions",
    "pins",
    "server-snapshot",
}

MEDIA_BUCKETS = {
    "screenshots",
    "charts",
    "docs",
    "brand-assets",
}


class DiscordArchiveError(RuntimeError):
    """Base error for archive workflow failures."""


class DiscordCredentialError(DiscordArchiveError):
    """Raised when a required bot token is missing."""


class DiscordAPIError(DiscordArchiveError):
    """Raised when Discord returns an HTTP/API error."""


@dataclass(frozen=True)
class DiscordRestClient:
    """Small stdlib Discord REST client for read-only archive calls."""

    token: str
    base_url: str = API_BASE
    user_agent: str = "coinfox-discord-archive/0.1"

    def me(self) -> dict[str, Any]:
        return _ensure_dict(self.get("/users/@me"))

    def guild(self, guild_id: str) -> dict[str, Any]:
        return _ensure_dict(self.get(f"/guilds/{guild_id}"))

    def guild_channels(self, guild_id: str) -> list[dict[str, Any]]:
        return _ensure_list_of_dicts(self.get(f"/guilds/{guild_id}/channels"))

    def guild_roles(self, guild_id: str) -> list[dict[str, Any]]:
        return _ensure_list_of_dicts(self.get(f"/guilds/{guild_id}/roles"))

    def guild_invites(self, guild_id: str) -> list[dict[str, Any]]:
        return _ensure_list_of_dicts(self.get(f"/guilds/{guild_id}/invites"))

    def channel(self, channel_id: str) -> dict[str, Any]:
        return _ensure_dict(self.get(f"/channels/{channel_id}"))

    def channel_messages(
        self, channel_id: str, *, before: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"limit": str(max(1, min(limit, 100)))}
        if before:
            params["before"] = before
        return _ensure_list_of_dicts(self.get(f"/channels/{channel_id}/messages", params=params))

    def get(self, path: str, *, params: dict[str, str] | None = None) -> Any:
        url = self._url(path, params=params)
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bot {self.token}",
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
        )
        return self._open_json(request)

    def download_file(self, url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                destination.write_bytes(response.read())
        except urllib.error.HTTPError as exc:
            raise DiscordAPIError(f"download failed: HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise DiscordAPIError(f"download failed: {exc.reason}") from exc

    def _url(self, path: str, *, params: dict[str, str] | None = None) -> str:
        path = "/" + path.lstrip("/")
        url = self.base_url.rstrip("/") + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def _open_json(self, request: urllib.request.Request) -> Any:
        for attempt in range(2):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                    body = response.read().decode("utf-8")
                    return json.loads(body) if body else None
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code == 429 and attempt == 0:
                    retry_after = _retry_after_seconds(body)
                    time.sleep(min(retry_after, 5.0))
                    continue
                raise DiscordAPIError(_discord_error_message(exc.code, body)) from exc
            except urllib.error.URLError as exc:
                raise DiscordAPIError(f"discord request failed: {exc.reason}") from exc
        raise DiscordAPIError("discord request failed after retry")


def bot_token_from_env(env: dict[str, str] | None = None) -> str:
    values = os.environ if env is None else env
    token = (values.get(BOT_TOKEN_ENV) or "").strip()
    if not token:
        raise DiscordCredentialError(
            f"{BOT_TOKEN_ENV} is required; legacy {LEGACY_USER_TOKEN_ENV} is ignored"
        )
    return token


def create_scaffold(root: str | Path) -> Path:
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    for bucket in EXPORT_BUCKETS:
        (root_path / "exports" / bucket).mkdir(parents=True, exist_ok=True)
    for bucket in MEDIA_BUCKETS:
        (root_path / "media" / bucket).mkdir(parents=True, exist_ok=True)
    (root_path / "settings").mkdir(parents=True, exist_ok=True)

    _write_if_missing(
        root_path / "README.md",
        "\n".join(
            [
                "# CoinFox Discord Private Archive",
                "",
                "Status: Phase 1-3 archive in progress.",
                "",
                "Stop line: verify this archive before channel cleanup or public invites.",
                "",
            ]
        ),
    )
    _write_if_missing(
        root_path / "redaction-log.md",
        "# Redaction Log\n\nRecord deliberate private omissions here without copying secrets.\n",
    )
    _write_if_missing(
        root_path / "founder-footnotes.md",
        "# Founder Footnotes\n\nPrivate creation notes and origin context go here.\n",
    )
    _write_tracker_header(root_path / "channel_decision_tracker.csv")
    if not (root_path / "manifest.json").exists():
        write_manifest(root_path, _default_manifest())
    return root_path


def doctor(root: str | Path, *, env: dict[str, str] | None = None) -> dict[str, Any]:
    values = os.environ if env is None else env
    root_path = Path(root)
    return {
        "archive_root": str(root_path),
        "archive_root_exists": root_path.exists(),
        "manifest_exists": (root_path / "manifest.json").exists(),
        "tracker_exists": (root_path / "channel_decision_tracker.csv").exists(),
        "checksums_exists": (root_path / "checksums.sha256").exists(),
        "bot_token_present": bool((values.get(BOT_TOKEN_ENV) or "").strip()),
        "bot_token_env": BOT_TOKEN_ENV,
        "legacy_user_token_ignored": LEGACY_USER_TOKEN_ENV in values,
        "legacy_user_token_env": LEGACY_USER_TOKEN_ENV,
        "mutating_commands_available": False,
    }


def snapshot_guild(root: str | Path, client: Any, guild_id: str) -> dict[str, Any]:
    root_path = create_scaffold(root)
    snapshot = {
        "bot_user": client.me(),
        "guild": client.guild(guild_id),
        "channels": client.guild_channels(guild_id),
        "roles": client.guild_roles(guild_id),
        "invites": client.guild_invites(guild_id),
    }
    settings_path = root_path / "settings" / "discord_snapshot.json"
    write_json(settings_path, snapshot)

    manifest = read_manifest(root_path)
    settings_files = list(manifest.get("settings_files") or [])
    _append_unique(settings_files, "settings/discord_snapshot.json")
    manifest["settings_files"] = settings_files
    manifest["status"] = "phase_1_3_archive_in_progress"
    write_manifest(root_path, manifest)

    return {
        "guild_id": guild_id,
        "settings_file": "settings/discord_snapshot.json",
        "channels": len(snapshot["channels"]),
        "roles": len(snapshot["roles"]),
        "invites": len(snapshot["invites"]),
    }


def export_channel(
    root: str | Path,
    client: Any,
    *,
    channel_id: str,
    bucket: str,
    max_messages: int = 1000,
    include_attachments: bool = True,
) -> dict[str, Any]:
    if bucket not in EXPORT_BUCKETS:
        raise ValueError(f"unsupported export bucket: {bucket}")
    root_path = create_scaffold(root)
    channel = client.channel(channel_id)
    channel_name = str(channel.get("name") or channel_id)
    safe_channel = safe_component(f"{channel_name}_{channel_id}")

    messages = _fetch_messages(client, channel_id=channel_id, max_messages=max_messages)
    messages = _sort_messages_oldest_first(messages)

    export_rel = Path("exports") / bucket / f"{safe_channel}.json"
    media_rel = Path("media") / "screenshots" / safe_channel
    attachments_saved = 0
    if include_attachments:
        attachments_saved = _download_attachments(root_path, client, safe_channel, messages)

    export_payload = {
        "channel": channel,
        "message_count": len(messages),
        "messages": messages,
    }
    write_json(root_path / export_rel, export_payload)

    pins_saved = "none_found"
    attachments_status = "yes" if attachments_saved else "none_found"
    upsert_manifest_channel(
        root_path,
        {
            "channel": channel_name,
            "channel_id": channel_id,
            "category": "",
            "date_range": _date_range(messages),
            "export_file": _rel(export_rel),
            "media_path": _rel(media_rel),
            "pins_saved": pins_saved,
            "attachments_saved": attachments_status,
            "export_method": "discord_rest_bot_token",
            "decision_tracker_status": "exported",
        },
    )
    upsert_tracker_row(
        root_path,
        {
            "channel_name": channel_name,
            "category": "",
            "archive_status": "exported",
            "pins_saved": pins_saved,
            "attachments_saved": attachments_status,
            "decision": "review_later",
            "public_after_reset": "private_staging",
            "notes": "exported by coinfox_discord_archive.py",
        },
    )
    return {
        "channel_id": channel_id,
        "channel": channel_name,
        "export_file": _rel(export_rel),
        "message_count": len(messages),
        "attachments_saved": attachments_saved,
    }


def upsert_manifest_channel(root: str | Path, entry: dict[str, Any]) -> None:
    root_path = Path(root)
    manifest = read_manifest(root_path)
    channels = list(manifest.get("channels") or [])
    key = str(entry.get("channel_id") or entry.get("channel") or "")
    replaced = False
    for index, existing in enumerate(channels):
        existing_key = str(existing.get("channel_id") or existing.get("channel") or "")
        if existing_key == key:
            channels[index] = {**existing, **entry}
            replaced = True
            break
    if not replaced:
        channels.append(entry)
    manifest["channels"] = channels
    manifest["status"] = "phase_1_3_archive_in_progress"
    write_manifest(root_path, manifest)


def upsert_tracker_row(root: str | Path, row: dict[str, str]) -> None:
    root_path = Path(root)
    tracker_path = root_path / "channel_decision_tracker.csv"
    _write_tracker_header(tracker_path)
    rows = _read_tracker_rows(tracker_path)
    normalized = {key: str(row.get(key, "")) for key in TRACKER_HEADER}
    replaced = False
    for index, existing in enumerate(rows):
        if existing.get("channel_name") == normalized["channel_name"]:
            rows[index] = normalized
            replaced = True
            break
    if not replaced:
        rows.append(normalized)
    with tracker_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=TRACKER_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def write_checksums(root: str | Path) -> dict[str, Any]:
    root_path = Path(root)
    checksum_path = root_path / "checksums.sha256"
    lines: list[str] = []
    for path in _archive_files(root_path):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {_rel(path.relative_to(root_path))}")
    checksum_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return {"checksum_file": "checksums.sha256", "file_count": len(lines)}


def verify_checksums(root: str | Path) -> list[str]:
    root_path = Path(root)
    checksum_path = root_path / "checksums.sha256"
    if not checksum_path.exists():
        return ["MISSING checksums.sha256"]
    failures: list[str] = []
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(maxsplit=1)
        path = root_path / relative
        if not path.exists():
            failures.append(f"MISSING {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual.lower() != expected.lower():
            failures.append(f"MISMATCH {relative}")
    return failures


def stop_gate_report(root: str | Path) -> dict[str, Any]:
    root_path = Path(root)
    manifest = read_manifest(root_path) if (root_path / "manifest.json").exists() else {}
    tracker_rows = (
        _read_tracker_rows(root_path / "channel_decision_tracker.csv")
        if (root_path / "channel_decision_tracker.csv").exists()
        else []
    )
    checks = {
        "archive_folder_has_exports": _has_non_readme_file(root_path / "exports"),
        "important_pins_saved": _has_non_readme_file(root_path / "exports" / "pins")
        or _settings_file_has_body(root_path / "settings" / "pins-before-reset.md"),
        "important_media_saved": _has_non_readme_file(root_path / "media"),
        "manifest_updated": bool(manifest.get("channels")),
        "channel_decision_tracker_updated": bool(tracker_rows),
        "checksums_generated": (root_path / "checksums.sha256").exists(),
        "archive_opens_locally": root_path.exists() and (root_path / "manifest.json").exists(),
        "founder_footnotes_available": _settings_file_has_body(root_path / "founder-footnotes.md"),
    }
    checks["checksum_verification_passes"] = checks["checksums_generated"] and not verify_checksums(
        root_path
    )
    ready = all(checks.values())
    return {
        "ready": ready,
        "checks": checks,
        "manual_checks": ["no_public_invites_active"],
    }


def read_manifest(root: str | Path) -> dict[str, Any]:
    path = Path(root) / "manifest.json"
    if not path.exists():
        return _default_manifest()
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(root: str | Path, manifest: dict[str, Any]) -> None:
    write_json(Path(root) / "manifest.json", manifest)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_component(value: str) -> str:
    cleaned = []
    for char in value:
        if char.isalnum() or char in {"-", "_", "."}:
            cleaned.append(char)
        else:
            cleaned.append("-")
    result = "".join(cleaned).strip(".-_")
    return result or "unnamed"


def _default_manifest() -> dict[str, Any]:
    return {
        "archive_name": "CoinFox_Discord_Archive_2026-06-24",
        "created_for": "CoinFox Discord reset",
        "status": "phase_1_3_archive_in_progress",
        "contains_private_material": True,
        "public_safe": False,
        "git_tracked": False,
        "checksum_file": "checksums.sha256",
        "notes": [
            "Phase 1-3 only: freeze invites, export/archive, fill manifest/tracker, "
            "verify checksums.",
            "No channel cleanup, channel movement, or public invite creation before "
            "archive verification.",
        ],
        "channels": [],
        "settings_files": [],
    }


def _fetch_messages(client: Any, *, channel_id: str, max_messages: int) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    before: str | None = None
    remaining = max(0, max_messages)
    while remaining:
        limit = min(100, remaining)
        page = client.channel_messages(channel_id, before=before, limit=limit)
        if not page:
            break
        messages.extend(page)
        remaining -= len(page)
        before = str(page[-1].get("id") or "")
        if len(page) < limit:
            break
    return messages


def _download_attachments(
    root: Path, client: Any, safe_channel: str, messages: list[dict[str, Any]]
) -> int:
    count = 0
    for message in messages:
        for attachment in message.get("attachments") or []:
            if not isinstance(attachment, dict):
                continue
            url = str(attachment.get("url") or "")
            filename = safe_component(Path(str(attachment.get("filename") or "attachment")).name)
            if not url or not filename:
                continue
            media_bucket = _media_bucket(attachment)
            destination = _unique_destination(
                root / "media" / media_bucket / safe_channel / filename
            )
            client.download_file(url, destination)
            count += 1
    return count


def _media_bucket(attachment: dict[str, Any]) -> str:
    filename = str(attachment.get("filename") or "").lower()
    content_type = str(attachment.get("content_type") or "").lower()
    if content_type.startswith("image/") or filename.endswith(
        (".png", ".jpg", ".jpeg", ".gif", ".webp")
    ):
        return "screenshots"
    return "docs"


def _unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 10_000):
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise DiscordArchiveError(f"could not create unique filename for {path.name}")


def _sort_messages_oldest_first(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(message: dict[str, Any]) -> tuple[int, str]:
        raw_id = str(message.get("id") or "0")
        try:
            return (int(raw_id), raw_id)
        except ValueError:
            return (0, raw_id)

    return sorted(messages, key=key)


def _date_range(messages: list[dict[str, Any]]) -> str:
    timestamps = [str(message.get("timestamp")) for message in messages if message.get("timestamp")]
    if not timestamps:
        return ""
    return f"{timestamps[0]} through {timestamps[-1]}"


def _archive_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.name != "checksums.sha256"
    )


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _write_tracker_header(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(TRACKER_HEADER)


def _read_tracker_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != list(TRACKER_HEADER):
            return []
        return [dict(row) for row in reader]


def _has_non_readme_file(path: Path) -> bool:
    if not path.exists():
        return False
    for candidate in path.rglob("*"):
        if candidate.is_file() and candidate.name.lower() != "readme.md":
            return True
    return False


def _settings_file_has_body(path: Path) -> bool:
    if not path.exists():
        return False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if _is_meaningful_table_row(line):
            return True
        if line.startswith("|"):
            continue
        lowered = line.lower()
        if lowered.startswith("private creation notes"):
            continue
        if "go here" in lowered or lowered.startswith("record "):
            continue
        if lowered.startswith("do not paste "):
            continue
        if "public-facing summaries" in lowered or "unredacted private" in lowered:
            continue
        return True
    return False


def _is_meaningful_table_row(line: str) -> bool:
    if not line.startswith("|"):
        return False
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    if not any(cells):
        return False
    lowered = [cell.lower() for cell in cells]
    if all(set(cell) <= {"-"} for cell in lowered if cell):
        return False
    header_terms = {
        "category",
        "channel",
        "pin summary",
        "export path or screenshot path",
        "keep public?",
        "notes",
    }
    if all(cell in header_terms for cell in lowered if cell):
        return False
    return True


def _rel(path: Path) -> str:
    return path.as_posix()


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _ensure_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DiscordAPIError("discord response was not an object")
    return value


def _ensure_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise DiscordAPIError("discord response was not a list of objects")
    return value


def _retry_after_seconds(body: str) -> float:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return 1.0
    try:
        return float(payload.get("retry_after") or 1.0)
    except (TypeError, ValueError):
        return 1.0


def _discord_error_message(status: int, body: str) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return f"discord request failed: HTTP {status}"
    message = str(payload.get("message") or f"HTTP {status}")
    code = payload.get("code")
    if code is not None:
        return f"discord request failed: HTTP {status} code {code}: {message}"
    return f"discord request failed: HTTP {status}: {message}"
