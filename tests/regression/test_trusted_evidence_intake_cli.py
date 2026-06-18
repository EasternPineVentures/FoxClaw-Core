from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INTAKE_TOOL = REPO / "tools" / "forecast_evidence_intake.py"


def test_trusted_evidence_intake_cli_writes_packet_and_validation_receipts(tmp_path):
    db = tmp_path / "forecast_desk.db"
    completed = subprocess.run(
        [
            sys.executable,
            str(INTAKE_TOOL),
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

    assert payload["status"] == "accepted"
    assert payload["accepted_for_dossier"] is True
    assert payload["authority"] == {
        "authority_level": "context_only",
        "can_authorize_execution": False,
        "can_enter_paper": False,
        "can_move_funds": False,
        "can_publish": False,
        "can_set_probability": False,
        "can_submit_order": False,
        "live_execution_allowed": False,
    }
    assert payload["counts"]["trusted_evidence_packets"] == 1
    assert payload["counts"]["trusted_evidence_validations"] == 1

    with sqlite3.connect(str(db)) as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        packet = conn.execute(
            """
            SELECT authority_level, can_set_probability, can_publish, can_enter_paper,
                   can_submit_order, can_move_funds, live_execution_allowed
            FROM trusted_evidence_packets
            """
        ).fetchone()
        validation = conn.execute(
            """
            SELECT status, accepted_for_dossier, can_authorize_execution,
                   can_publish, can_enter_paper, can_submit_order,
                   can_move_funds, live_execution_allowed
            FROM trusted_evidence_validations
            """
        ).fetchone()

    assert version == 3
    assert packet == ("context_only", 0, 0, 0, 0, 0, 0)
    assert validation == ("accepted", 1, 0, 0, 0, 0, 0, 0)
