from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from foxclaw.apollo1_intake import build_report, load_manifest

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "apollo1_intake.py"


def test_apollo1_intake_report_marks_a1_continuity_ready():
    report = build_report(generated_at=datetime(2026, 6, 29, 15, 0, tzinfo=UTC))

    assert report["schema_version"] == "apollo1_intake_report.v0"
    assert report["readiness_status"] == "a1_continuity_ready"
    assert report["required_for_a1_continuity"] == {
        "total": 5,
        "ready": 5,
        "not_ready": 0,
    }
    assert report["blocked"] == []
    assert report["authority"]["can_submit_order"] is False
    assert report["authority"]["can_publish_to_coinfox"] is False


def test_apollo1_intake_ready_lanes_include_packet_guard_and_metadata():
    report = build_report(generated_at=datetime(2026, 6, 29, 15, 0, tzinfo=UTC))
    ready_ids = {lane["id"] for lane in report["a1_ready_lanes"]}

    assert "source_discovery_inventory" in ready_ids
    assert "interaction_potential_scoring" in ready_ids
    assert "manual_public_packet_intake" in ready_ids
    assert "source_registry_guard" in ready_ids
    assert "packet_soak_and_trust_metadata" in ready_ids
    packet_lane = next(lane for lane in report["lanes"] if lane["id"] == "manual_public_packet_intake")
    assert "--trust-metadata" in packet_lane["proof_command"]
    assert packet_lane["ready_without_a2"] is True
    assert packet_lane["apollo2_required"] is False


def test_apollo1_intake_defers_legacy_discord_parser_to_a2():
    report = build_report(generated_at=datetime(2026, 6, 29, 15, 0, tzinfo=UTC))
    deferred = {lane["id"]: lane for lane in report["deferred_to_a2"]}

    assert "apollo2_legacy_discord_parser" in deferred
    assert deferred["apollo2_legacy_discord_parser"]["ready_without_a2"] is False
    assert "Do not connect Discord" in deferred["apollo2_legacy_discord_parser"]["operator_action"]
    assert "live_source_automation" in deferred


def test_apollo1_intake_cli_fixture_json_is_parseable():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["generated_at"] == "2026-06-29T15:00:00Z"
    assert payload["readiness_status"] == "a1_continuity_ready"
    assert payload["required_for_a1_continuity"]["not_ready"] == 0
    assert payload["deferred_to_a2"][0]["apollo2_required"] is True


def test_apollo1_intake_cli_fixture_markdown_names_authority_locks():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "# Apollo 1 Standalone Intake" in completed.stdout
    assert "Readiness: `a1_continuity_ready`" in completed.stdout
    assert "`can_publish_to_coinfox=false`" in completed.stdout
    assert "apollo2_legacy_discord_parser" in completed.stdout


def test_apollo1_intake_manifest_rejects_unsafe_proof_commands(tmp_path):
    manifest = {
        "schema_version": "apollo1_intake_lanes.v0",
        "generated_for": "apollo1_standalone_intake",
        "authority": {
            "can_submit_order": False,
            "can_move_funds": False,
            "live_execution_allowed": False,
            "can_publish_to_coinfox": False,
            "can_change_source_reliability": False,
            "can_update_verified_memory": False,
        },
        "lanes": [
            {
                "id": "unsafe",
                "name": "Unsafe",
                "status": "planned",
                "required_for_a1_continuity": False,
                "ready_without_a2": True,
                "apollo2_required": False,
                "source_mode": "test",
                "purpose": "prove rejection",
                "operator_action": "reject",
                "proof_command": "python tool.py --live",
                "safety_boundary": "unsafe",
            }
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="unsafe fragment"):
        load_manifest(path)
