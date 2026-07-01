from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from foxclaw.contract.public.coinfox_packet import render_coinfox_curated_packet_markdown

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "coinfox_packet_demo.py"
FIXTURE = REPO / "tests" / "fixtures" / "public_contract" / "coinfox_curated_packet.valid.json"
INTAKE_FIXTURE = (
    REPO / "tests" / "fixtures" / "coinfox_packet_intake" / "manual_market_pulse_intake.valid.json"
)


def test_render_coinfox_curated_packet_names_cards_and_authority():
    packet = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rendered = render_coinfox_curated_packet_markdown(packet)

    assert "# CoinFox Curated Packet" in rendered
    assert "market_pulse_now" in rendered
    assert "WEN retail attention" in rendered
    assert "Prediction-market odds shift" in rendered
    assert "BTC discussion shifted" in rendered
    assert "review_priority_only" in rendered
    assert "Live execution allowed: `false`" in rendered


def test_coinfox_packet_demo_cli_fixture_markdown():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "# CoinFox Curated Packet" in completed.stdout
    assert "Public links and summaries only" in completed.stdout
    assert "Private lineage excluded: `true`" in completed.stdout
    assert "Can submit order: `false`" in completed.stdout


def test_coinfox_packet_demo_cli_fixture_json():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["schema_version"] == "coinfox_curated_packet.v1"
    assert payload["packet_type"] == "market_pulse_now"
    assert payload["status"]["live_execution_allowed"] is False
    assert len(payload["cards"]) == 3


def test_coinfox_packet_demo_cli_fixture_with_intake_guard():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--intake", str(INTAKE_FIXTURE)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "# CoinFox Curated Packet" in completed.stdout
    assert "cfpacket_market_pulse_20260627_fixture" in completed.stdout
    assert "quarantined" not in completed.stdout.lower()
