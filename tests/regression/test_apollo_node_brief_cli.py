from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BRIEF_TOOL = REPO / "tools" / "apollo_node_brief.py"


def test_apollo_node_brief_cli_fixture_json_is_safe_and_parseable():
    completed = subprocess.run(
        [
            sys.executable,
            str(BRIEF_TOOL),
            "--fixture",
            "--node-id",
            "A1",
            "--peer-node",
            "A2",
            "--current-slice",
            "fixture coordination",
            "--next-request",
            "pull and continue",
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["protocol"] == "apollo_node_brief_v1"
    assert payload["node_id"] == "A1"
    assert payload["peer_node"] == "A2"
    assert payload["git"]["dirty"] is False
    assert payload["git"]["head"] == "fixture"
    assert payload["authority"] == {
        "can_move_funds": False,
        "can_publish": False,
        "can_set_probability": False,
        "can_submit_order": False,
        "live_execution_allowed": False,
    }
    assert payload["next_request"] == "pull and continue"


def test_apollo_node_brief_cli_fixture_markdown_names_peer():
    completed = subprocess.run(
        [
            sys.executable,
            str(BRIEF_TOOL),
            "--fixture",
            "--node-id",
            "A2",
            "--peer-node",
            "A1",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "# FoxClaw Apollo Node Brief" in completed.stdout
    assert "From: `A2`" in completed.stdout
    assert "To: `A1`" in completed.stdout
    assert "`can_submit_order=false`" in completed.stdout
