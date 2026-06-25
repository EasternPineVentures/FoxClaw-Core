from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from foxclaw.adapters.discord import archive

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "coinfox_discord_archive.py"


class FakeDiscordClient:
    def __init__(self) -> None:
        self.downloads: list[tuple[str, Path]] = []
        self.message_calls: list[tuple[str, str | None]] = []

    def me(self) -> dict[str, object]:
        return {"id": "bot_1", "username": "CoinFoxArchive"}

    def guild(self, guild_id: str) -> dict[str, object]:
        return {"id": guild_id, "name": "Legacy Fox Room"}

    def guild_channels(self, guild_id: str) -> list[dict[str, object]]:
        return [
            {"id": "chan_founder", "name": "founder-notes", "type": 0, "parent_id": "cat_private"},
            {"id": "chan_signal", "name": "btc-signals", "type": 0, "parent_id": "cat_signals"},
        ]

    def guild_roles(self, guild_id: str) -> list[dict[str, object]]:
        return [
            {"id": "role_founder", "name": "Founder", "permissions": "8"},
            {"id": "role_member", "name": "Member", "permissions": "0"},
        ]

    def guild_invites(self, guild_id: str) -> list[dict[str, object]]:
        return [{"code": "private-old", "channel": {"id": "chan_founder", "name": "founder-notes"}}]

    def channel(self, channel_id: str) -> dict[str, object]:
        return {"id": channel_id, "name": "btc-signals", "parent_id": "cat_signals"}

    def channel_messages(
        self, channel_id: str, *, before: str | None = None, limit: int = 100
    ) -> list[dict[str, object]]:
        self.message_calls.append((channel_id, before))
        if before is not None:
            return []
        return [
            {
                "id": "200",
                "timestamp": "2026-06-24T12:05:00+00:00",
                "content": "entry idea",
                "author": {"id": "user_private", "username": "Founder"},
                "attachments": [
                    {
                        "id": "att_1",
                        "filename": "../chart.png",
                        "url": "https://cdn.discordapp.example/chart.png",
                        "content_type": "image/png",
                    },
                    {
                        "id": "att_2",
                        "filename": "notes.pdf",
                        "url": "https://cdn.discordapp.example/notes.pdf",
                        "content_type": "application/pdf",
                    },
                ],
            },
            {
                "id": "100",
                "timestamp": "2026-06-24T12:00:00+00:00",
                "content": "older context",
                "author": {"id": "user_private", "username": "Founder"},
                "attachments": [],
            },
        ]

    def download_file(self, url: str, destination: Path) -> None:
        self.downloads.append((url, destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(f"downloaded {url}".encode("utf-8"))


def test_create_scaffold_writes_phase_templates_without_checksums(tmp_path: Path) -> None:
    archive.create_scaffold(tmp_path)

    assert (tmp_path / "manifest.json").exists()
    tracker_header = (tmp_path / "channel_decision_tracker.csv").read_text(
        encoding="utf-8"
    ).splitlines()
    assert tracker_header == [
        "channel_name,category,archive_status,pins_saved,attachments_saved,"
        "decision,public_after_reset,notes"
    ]
    assert (tmp_path / "exports" / "founder-notes").is_dir()
    assert (tmp_path / "exports" / "signal-history").is_dir()
    assert (tmp_path / "media" / "screenshots").is_dir()
    assert (tmp_path / "media" / "brand-assets").is_dir()
    assert not (tmp_path / "checksums.sha256").exists()

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["contains_private_material"] is True
    assert manifest["public_safe"] is False
    assert manifest["git_tracked"] is False
    assert manifest["status"] == "phase_1_3_archive_in_progress"


def test_snapshot_writes_server_metadata_without_mutating_discord(tmp_path: Path) -> None:
    archive.create_scaffold(tmp_path)
    result = archive.snapshot_guild(tmp_path, FakeDiscordClient(), "guild_1")

    assert result["guild_id"] == "guild_1"
    assert result["channels"] == 2
    assert result["roles"] == 2
    assert result["invites"] == 1

    snapshot = json.loads(
        (tmp_path / "settings" / "discord_snapshot.json").read_text(encoding="utf-8")
    )
    assert snapshot["guild"]["name"] == "Legacy Fox Room"
    assert snapshot["bot_user"]["username"] == "CoinFoxArchive"
    assert [channel["name"] for channel in snapshot["channels"]] == ["founder-notes", "btc-signals"]

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert "settings/discord_snapshot.json" in manifest["settings_files"]


def test_export_channel_writes_messages_media_manifest_and_tracker(tmp_path: Path) -> None:
    archive.create_scaffold(tmp_path)
    client = FakeDiscordClient()

    result = archive.export_channel(
        tmp_path,
        client,
        channel_id="chan_signal",
        bucket="signal-history",
        max_messages=100,
        include_attachments=True,
    )

    assert result["message_count"] == 2
    assert result["attachments_saved"] == 2
    assert client.message_calls == [("chan_signal", None)]
    assert [path.name for _, path in client.downloads] == ["chart.png", "notes.pdf"]

    export_file = tmp_path / "exports" / "signal-history" / "btc-signals_chan_signal.json"
    payload = json.loads(export_file.read_text(encoding="utf-8"))
    assert [message["id"] for message in payload["messages"]] == ["100", "200"]
    assert payload["channel"]["name"] == "btc-signals"

    assert (tmp_path / "media" / "screenshots" / "btc-signals_chan_signal" / "chart.png").exists()
    assert (tmp_path / "media" / "docs" / "btc-signals_chan_signal" / "notes.pdf").exists()

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["channels"][0]["channel"] == "btc-signals"
    assert (
        manifest["channels"][0]["export_file"]
        == "exports/signal-history/btc-signals_chan_signal.json"
    )
    assert manifest["channels"][0]["attachments_saved"] == "yes"

    tracker_lines = (tmp_path / "channel_decision_tracker.csv").read_text(
        encoding="utf-8"
    ).splitlines()
    assert tracker_lines[1].startswith(
        "btc-signals,,exported,none_found,yes,review_later,private_staging,"
    )


def test_checksum_generation_and_verification_detects_mismatch(tmp_path: Path) -> None:
    archive.create_scaffold(tmp_path)
    (tmp_path / "exports" / "founder-notes" / "note.txt").write_text("saved", encoding="utf-8")

    summary = archive.write_checksums(tmp_path)

    assert summary["file_count"] > 0
    checksum_file = tmp_path / "checksums.sha256"
    assert checksum_file.exists()
    assert "checksums.sha256" not in checksum_file.read_text(encoding="utf-8")
    assert archive.verify_checksums(tmp_path) == []

    (tmp_path / "exports" / "founder-notes" / "note.txt").write_text("changed", encoding="utf-8")

    failures = archive.verify_checksums(tmp_path)
    assert failures == ["MISMATCH exports/founder-notes/note.txt"]


def test_stop_gate_blocks_empty_archive_and_passes_after_required_evidence(tmp_path: Path) -> None:
    archive.create_scaffold(tmp_path)

    blocked = archive.stop_gate_report(tmp_path)
    assert blocked["ready"] is False
    assert blocked["checks"]["archive_folder_has_exports"] is False
    assert blocked["checks"]["checksums_generated"] is False
    assert blocked["checks"]["important_pins_saved"] is False
    assert blocked["checks"]["founder_footnotes_available"] is False

    (tmp_path / "exports" / "founder-notes" / "note.txt").write_text("saved", encoding="utf-8")
    (tmp_path / "exports" / "pins" / "pins.txt").write_text("pins", encoding="utf-8")
    (tmp_path / "media" / "screenshots" / "chart.png").write_bytes(b"image")
    (tmp_path / "founder-footnotes.md").write_text(
        "# Founder Footnotes\n\nOrigin.", encoding="utf-8"
    )
    archive.upsert_manifest_channel(
        tmp_path,
        {
            "channel": "founder-notes",
            "category": "private",
            "export_file": "exports/founder-notes/note.txt",
            "media_path": "media/screenshots",
        },
    )
    archive.upsert_tracker_row(
        tmp_path,
        {
            "channel_name": "founder-notes",
            "category": "private",
            "archive_status": "verified",
            "pins_saved": "yes",
            "attachments_saved": "yes",
            "decision": "review_later",
            "public_after_reset": "private_staging",
            "notes": "phase gate fixture",
        },
    )
    archive.write_checksums(tmp_path)

    ready = archive.stop_gate_report(tmp_path)
    assert ready["ready"] is True


def test_cli_doctor_ignores_legacy_user_token_and_does_not_print_secret(
    tmp_path: Path,
) -> None:
    archive.create_scaffold(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--archive-root",
            str(tmp_path),
            "doctor",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
        env={"USER_TOKEN": "legacy-user-token-do-not-port", "PYTHONPATH": str(REPO)},
    )

    payload = json.loads(completed.stdout)
    assert payload["archive_root_exists"] is True
    assert payload["bot_token_present"] is False
    assert payload["legacy_user_token_ignored"] is True
    assert "legacy-user-token-do-not-port" not in completed.stdout
    assert "legacy-user-token-do-not-port" not in completed.stderr
