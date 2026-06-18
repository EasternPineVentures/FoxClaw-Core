from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.freeze_forecast_db_schema import FROZEN_JSON, current_artifact

REPO = Path(__file__).resolve().parents[2]


def test_forecast_schema_frozen_artifact_matches_current_schema():
    frozen = json.loads(FROZEN_JSON.read_text(encoding="utf-8"))
    current = current_artifact()
    assert frozen["fingerprint"] == current["fingerprint"]
    assert frozen["schema"]["schema_version"] == 2
    assert "raw_payloads" in frozen["schema"]["tables"]
    assert "market_snapshots" in frozen["schema"]["tables"]
    assert "forecast_receipts" in frozen["schema"]["tables"]


def test_freeze_forecast_schema_check_command_passes():
    completed = subprocess.run(
        [sys.executable, "tools/freeze_forecast_db_schema.py", "--check"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "[forecast-schema] OK" in completed.stdout
