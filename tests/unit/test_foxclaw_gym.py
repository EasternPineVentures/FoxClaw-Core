from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from foxclaw.gym import build_report, load_manifest

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "foxclaw_gym.py"


def test_gym_report_keeps_demo_deadline_and_authority_locks():
    report = build_report(
        today=date(2026, 6, 19),
        generated_at=datetime(2026, 6, 19, 17, 30, tzinfo=UTC),
    )
    assert report["target_demo_date"] == "2026-06-28"
    assert report["days_remaining"] == 9
    assert report["readiness_status"] == "training"
    assert report["authority"] == {
        "can_submit_order": False,
        "can_move_funds": False,
        "live_execution_allowed": False,
    }
    assert report["demo_critical"]["blocked"] == 0
    assert report["demo_critical"]["not_ready"] > 0


def test_gym_next_attention_prioritizes_story_and_demo_surface():
    report = build_report(
        today=date(2026, 6, 19),
        generated_at=datetime(2026, 6, 19, 17, 30, tzinfo=UTC),
    )
    next_ids = [item["id"] for item in report["next_attention"]]
    assert next_ids[:3] == [
        "public_demo_threat_model",
        "coinfox_public_card_rehearsal",
        "planifier_practice_rehearsal",
    ]


def test_gym_knows_coinfox_is_social_not_just_cards():
    report = build_report(
        today=date(2026, 6, 19),
        generated_at=datetime(2026, 6, 19, 17, 30, tzinfo=UTC),
    )
    coinfox = next(item for item in report["drills"] if item["id"] == "coinfox_public_card_rehearsal")
    assert coinfox["name"] == "CoinFox Social Feed And Card"
    assert "existing but clunky" in coinfox["purpose"]
    assert "post ideas" in coinfox["demo_line"]
    assert "major work" in coinfox["demo_line"]


def test_gym_first_encounter_guide_is_ready():
    report = build_report(
        today=date(2026, 6, 19),
        generated_at=datetime(2026, 6, 19, 17, 30, tzinfo=UTC),
    )
    guide = next(item for item in report["drills"] if item["id"] == "family_demo_story")
    assert guide["name"] == "Visitor First Encounter"
    assert guide["status"] == "ready"
    assert "without needing a pitch" in guide["purpose"]


def test_gym_knows_planifier_exists_but_needs_work():
    report = build_report(
        today=date(2026, 6, 19),
        generated_at=datetime(2026, 6, 19, 17, 30, tzinfo=UTC),
    )
    planifier = next(item for item in report["drills"] if item["id"] == "planifier_practice_rehearsal")
    assert planifier["status"] == "practice"
    assert "already exists" in planifier["demo_line"]
    assert "existing Planifier app" in planifier["next_action"]


def test_gym_cli_fixture_json_is_parseable():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["schema_version"] == "foxclaw_gym_report.v0"
    assert payload["days_remaining"] == 9
    assert payload["authority"]["live_execution_allowed"] is False
    assert payload["next_attention"][0]["id"] == "public_demo_threat_model"


def test_gym_cli_fixture_markdown_names_authority_locks():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "# FoxClaw Gym" in completed.stdout
    assert "Target demo: `2026-06-28` (9 days remaining)" in completed.stdout
    assert "`live_execution_allowed=false`" in completed.stdout


def test_gym_manifest_rejects_unsafe_proof_commands(tmp_path):
    manifest = {
        "schema_version": "foxclaw_gym_drills.v0",
        "target_demo_date": "2026-06-28",
        "generated_for": "family_demo",
        "authority": {
            "can_submit_order": False,
            "can_move_funds": False,
            "live_execution_allowed": False,
        },
        "drills": [
            {
                "id": "unsafe",
                "name": "Unsafe",
                "lane": "security",
                "status": "planned",
                "demo_critical": True,
                "attention_rank": 1,
                "due_date": "2026-06-20",
                "purpose": "prove rejection",
                "proof_command": "python tool.py --live",
                "demo_line": "unsafe",
                "next_action": "reject",
            }
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="unsafe fragment"):
        load_manifest(path)
