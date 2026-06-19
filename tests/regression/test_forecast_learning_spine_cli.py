from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "forecast_learning_spine.py"


def test_forecast_learning_spine_fixture_records_learning_receipt(tmp_path: Path):
    db = tmp_path / "forecast_desk.db"
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--fixture",
            "--db",
            str(db),
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    receipt = payload["learning_receipt"]

    assert payload["recorded"] is True
    assert receipt["learning_signal"] == "reinforce"
    assert receipt["decision_quality"] == "foxclaw_outperformed_market"
    assert payload["authority"]["can_set_probability"] is False
    assert payload["authority"]["can_submit_order"] is False

    with sqlite3.connect(str(db)) as conn:
        row = conn.execute(
            """
            SELECT learning_signal, decision_quality, can_set_probability,
                   can_submit_order, live_execution_allowed
            FROM forecast_learning_receipts
            WHERE learning_receipt_id = ?
            """,
            (receipt["learning_receipt_id"],),
        ).fetchone()

    assert row == ("reinforce", "foxclaw_outperformed_market", 0, 0, 0)
