from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from foxclaw.adapters.event_contracts.publication import (
    assert_no_private_fields,
    build_public_export,
    public_forecast,
    write_public_export,
)

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "forecast_desk_export_public.py"


def test_public_forecast_has_paper_label_and_no_private_hash():
    item = public_forecast(
        {
            "market_id": "KXTEST",
            "side": "yes",
            "verdict": "paper",
            "independent_probability": "0.62",
            "market_probability": "0.43",
            "usable_edge": "0.19",
            "dossier_hash": "sha256:private",
        }
    )
    assert item["mode"] == "PAPER"
    assert "dossier_hash" not in item
    assert item["public_id"].startswith("sha256:")


def test_public_export_preserves_losing_resolved_forecasts():
    export = build_public_export(
        [
            {"market_id": "WIN", "side": "yes", "status": "resolved", "net_result": "1.00"},
            {"market_id": "LOSS", "side": "yes", "status": "resolved", "net_result": "-1.00"},
        ],
        scoreboard={"resolved_forecasts": 2},
    )
    assert export["mode"] == "PAPER"
    assert len(export["forecasts"]) == 2
    assert any(item["market_id"] == "LOSS" for item in export["forecasts"])
    assert export["export_hash"].startswith("sha256:")
    assert_no_private_fields(export)


def test_public_export_writes_expected_static_files(tmp_path):
    export = build_public_export(
        [{"market_id": "KXTEST", "side": "yes", "status": "open"}],
        scoreboard={"resolved_forecasts": 0},
    )
    written = write_public_export(export, tmp_path)
    assert set(written) == {
        "public_forecasts_json",
        "public_forecasts_md",
        "scoreboard_json",
        "scoreboard_md",
        "build_log",
    }
    build_log = json.loads(written["build_log"].read_text(encoding="utf-8"))
    assert build_log["mode"] == "PAPER"
    assert build_log["export_hash"] == export["export_hash"]


def test_public_export_cli_fixture(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--write", str(tmp_path), "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["export"]["mode"] == "PAPER"
    assert (tmp_path / "public_forecasts.json").exists()
    assert any(item["market_id"] == "KXLOSS" for item in payload["export"]["forecasts"])
