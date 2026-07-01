from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from foxclaw.command_center import build_report, discover_tools, find_command, load_catalog

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "foxclaw_commands.py"


def test_command_catalog_loads_with_locked_authority():
    catalog = load_catalog()

    assert catalog["schema_version"] == "foxclaw_commands.v0"
    assert catalog["authority"] == {
        "can_submit_order": False,
        "can_move_funds": False,
        "live_execution_allowed": False,
        "can_publish_to_coinfox": False,
        "can_change_truth": False,
        "can_change_source_reliability": False,
        "can_update_verified_memory": False,
        "can_train_model": False,
        "can_run_live_network": False,
    }


def test_command_catalog_has_unique_ids_and_real_runnable_tools():
    catalog = load_catalog()
    command_ids: list[str] = []
    for group in catalog["groups"]:
        for command in group["commands"]:
            command_ids.append(command["id"])
            if command["runnable"] and command["command"].startswith("python tools\\"):
                tool = command["command"].split()[1]
                assert (REPO / tool).exists()

    assert len(command_ids) == len(set(command_ids))
    assert "interaction-potential" in command_ids
    assert "source-discovery" in command_ids
    assert "full-tests" in command_ids


def test_build_report_can_filter_and_search():
    report = build_report(category="coinfox_packets")

    assert report["group_count"] == 1
    assert report["groups"][0]["id"] == "coinfox_packets"
    assert report["command_count"] >= 4

    search_report = build_report(search="reaction")
    command_ids = {
        command["id"]
        for group in search_report["groups"]
        for command in group["commands"]
    }
    assert "interaction-potential" in command_ids


def test_discover_tools_includes_all_current_python_tools():
    tools = discover_tools()
    names = {tool["name"] for tool in tools}

    assert "foxclaw_commands.py" in names
    assert "source_discovery_inventory.py" in names
    assert "interaction_potential.py" in names
    assert "coinfox_packet_demo.py" in names
    assert len(tools) >= 29


def test_find_command_returns_group_context():
    command = find_command("interaction-potential")

    assert command["group_id"] == "start_here"
    assert command["runnable"] is True
    assert "ranking" in command["safety"]


def test_command_center_cli_json_is_parseable():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["schema_version"] == "foxclaw_command_center_report.v0"
    assert payload["command_count"] >= 30
    assert payload["authority"]["can_run_live_network"] is False


def test_command_center_cli_show_and_list_ids():
    show = subprocess.run(
        [sys.executable, str(TOOL), "--show", "source-discovery"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    ids = subprocess.run(
        [sys.executable, str(TOOL), "--list-ids"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "# Source Discovery" in show.stdout
    assert "python tools\\source_discovery_inventory.py --limit 20" in show.stdout
    assert "source-discovery" in ids.stdout.splitlines()


def test_command_center_cli_all_tools_lists_tool_help():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--all-tools"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "## All Tool Scripts" in completed.stdout
    assert "tools\\interaction_potential.py" in completed.stdout
    assert "python tools\\interaction_potential.py --help" in completed.stdout


def test_command_center_refuses_manual_only_run():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--run", "interaction-potential-intake"],
        cwd=REPO,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 2
    assert "manual-only" in completed.stderr


def test_command_catalog_rejects_live_authority(tmp_path):
    catalog = json.loads((REPO / "config" / "foxclaw_commands.json").read_text(encoding="utf-8"))
    catalog["authority"]["can_run_live_network"] = True
    path = tmp_path / "bad_commands.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")

    with pytest.raises(ValueError, match="can_run_live_network=false"):
        load_catalog(path)
