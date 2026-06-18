from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_forecast_desk_doctor_reports_all_silence_reasons():
    completed = subprocess.run(
        [sys.executable, "tools/forecast_desk_doctor.py", "--fixture", "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    status = json.loads(completed.stdout)
    assert status["mode"] == "PAPER"
    assert status["can_submit_order"] is False
    assert "no_positive_usable_edge" in status["silence_reasons"]
    assert "api_rate_limited" in status["silence_reasons"]


def test_forecast_desk_watch_once_writes_status_and_releases_lock(tmp_path):
    status_file = tmp_path / "status.json"
    lock_file = tmp_path / "watch.lock"
    completed = subprocess.run(
        [
            sys.executable,
            "tools/forecast_desk_watch.py",
            "--once",
            "--fixture",
            "--status-file",
            str(status_file),
            "--lock-file",
            str(lock_file),
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    printed = json.loads(completed.stdout)
    written = json.loads(status_file.read_text(encoding="utf-8"))
    assert printed == written
    assert written["freshness_receipt"]["is_fresh"] is True
    assert lock_file.exists() is False
