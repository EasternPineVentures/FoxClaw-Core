from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "fixtures" / "kalshi"
TOOL = REPO / "tools" / "kalshi_api_desk.py"


def _run(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture-dir", str(FIXTURES), *args, "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_doctor_never_loads_credentials_or_authority():
    out = _run("doctor")
    assert out["credentials_loaded"] is False
    assert out["can_submit_order"] is False
    assert out["can_move_funds"] is False
    assert out["live_execution_allowed"] is False
    assert out["network_called"] is False


def test_markets_command_returns_normalized_decimal_strings():
    out = _run("markets", "--status", "open", "--limit", "5")
    market = out["markets"][0]
    assert market["market_id"] == "KXJOBLESS-26JUN18-T250"
    assert market["yes_bid"] == "0.4200"
    assert market["raw_payload_hash"].startswith("sha256:")


def test_orderbook_command_reconstructs_executable_book():
    out = _run("orderbook", "--ticker", "KXJOBLESS-26JUN18-T250")
    book = out["orderbook"]
    assert book["best_yes_bid"] == "0.4200"
    assert book["best_yes_ask"] == "0.4300"
    assert book["depth_yes_at_best"] == "13.00"
    assert book["is_tradeable"] is True
