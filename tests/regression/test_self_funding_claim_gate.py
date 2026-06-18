from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "forecast_desk_self_funding.py"


def test_self_funding_fixture_cli_denies_paper_claim(tmp_path):
    out = tmp_path / "self_funding.json"
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
    assert written["claim_allowed"] is False
    assert written["mode"] == "paper"
    assert "mode_not_allowed_for_verified_claim" in written["reasons"]
