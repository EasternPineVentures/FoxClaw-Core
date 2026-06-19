from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from foxclaw.visitor import build_visitor_guide, render_visitor_guide_markdown

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "foxclaw_visitor_guide.py"


def test_visitor_guide_is_not_pitchy_and_names_system_order():
    guide = build_visitor_guide(generated_at=datetime(2026, 6, 19, 18, 0, tzinfo=UTC))
    assert guide["not_a_pitch"] is True
    assert guide["order"] == ["FoxClaw", "CoinFox", "Planifier"]
    assert guide["sections"][1]["status"] == "bones exist, full social product needs major work"
    assert "already has the bones" in guide["sections"][1]["plain_language"]
    assert "Long-running calls" in guide["sections"][1]["what_to_notice"][2]
    assert guide["sections"][2]["status"] == "already built, needs work"
    assert "copy-trade button" in guide["sections"][2]["what_to_notice"][2]


def test_visitor_guide_markdown_is_plain_language():
    guide = build_visitor_guide(generated_at=datetime(2026, 6, 19, 18, 0, tzinfo=UTC))
    rendered = render_visitor_guide_markdown(guide)
    assert "This is not a pitch" in rendered
    assert "FoxClaw -> CoinFox -> Planifier" in rendered
    assert "posting trade ideas" in rendered
    assert "branching conversations" in rendered
    assert "paper-only" in rendered
    assert "no funds movement" in rendered


def test_visitor_guide_cli_fixture_json_is_parseable():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["schema_version"] == "foxclaw_visitor_guide.v0"
    assert payload["generated_at"] == "2026-06-19T18:00:00Z"
    assert payload["not_a_pitch"] is True


def test_visitor_guide_cli_fixture_markdown():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "# FoxClaw First Encounter" in completed.stdout
    assert "CoinFox is becoming the social place" in completed.stdout
