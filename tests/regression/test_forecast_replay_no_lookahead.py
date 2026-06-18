from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "forecast_desk_replay.py"


def test_fixture_replay_cli_writes_paper_manifest_without_live_authority(tmp_path):
    out = tmp_path / "manifest.json"
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--write", str(out), "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    printed = json.loads(completed.stdout)
    written = json.loads(out.read_text(encoding="utf-8"))
    assert printed == written
    assert written["mode"] == "PAPER"
    assert written["outcomes"][0]["can_submit_order"] is False
    assert written["outcomes"][0]["can_move_funds"] is False
