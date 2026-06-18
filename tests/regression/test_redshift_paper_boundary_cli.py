from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BOUNDARY_TOOL = REPO / "tools" / "redshift_paper_boundary.py"


def test_redshift_paper_boundary_fixture_emits_linked_safe_receipts():
    completed = subprocess.run(
        [
            sys.executable,
            str(BOUNDARY_TOOL),
            "--fixture",
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["boundary"] == "redshift_paper_boundary_v1"
    assert payload["mode"] == "PAPER"
    assert payload["linked"] is True
    assert payload["authority"] == {
        "can_move_funds": False,
        "can_mutate_foxclaw_decision": False,
        "foxclaw_can_submit_order": False,
        "live_execution_allowed": False,
        "redshift_can_submit_order": False,
        "redshift_capital_effect": "none",
    }
    assert payload["decision_export"]["authority_level"] == "foxclaw_decision_context_only"
    assert payload["redshift_execution"]["authority_level"] == "redshift_paper_rehearsal"
    assert payload["redshift_execution"]["live_order_id"] is None
    assert payload["redshift_execution"]["account_id"] is None
    assert payload["redshift_outcome"]["net_result"] == "2.2000"
