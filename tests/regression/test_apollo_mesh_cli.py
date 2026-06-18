from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MESH_TOOL = REPO / "tools" / "apollo_mesh.py"


def _run(*args: str, cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MESH_TOOL), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )


def test_apollo_mesh_cli_handoff_round_trips_to_inbox(tmp_path: Path):
    mesh_dir = tmp_path / "mesh"
    identity_file = mesh_dir / "identity.json"

    init = _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A1",
        "--fixture",
        "--json",
        "init",
    )
    public_identity = json.loads(init.stdout)
    assert public_identity["node_id"] == "A1"
    assert public_identity["secret_loaded"] is True
    assert "secret" not in public_identity

    sent = _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A1",
        "--fixture",
        "--json",
        "handoff",
        "--to-node",
        "A2",
        "--summary",
        "Redshift boundary is ready",
        "--current-slice",
        "apollo mesh v0",
        "--next-request",
        "pull and run the boundary fixture",
    )
    event = json.loads(sent.stdout)
    assert event["kind"] == "handoff.note"
    assert event["from_node"] == "A1"
    assert event["tags"] == ["to:A2"]
    assert event["authority"]["can_remote_command"] is False

    event_file = tmp_path / "event.json"
    event_file.write_text(sent.stdout, encoding="utf-8")
    received = _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A1",
        "--fixture",
        "--json",
        "receive",
        "--event-file",
        str(event_file),
    )
    assert json.loads(received.stdout)["received"] is True

    inbox = _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A1",
        "--fixture",
        "--json",
        "inbox",
    )
    payload = json.loads(inbox.stdout)
    assert payload["count"] == 1
    assert payload["events"][0]["event_id"] == event["event_id"]


def test_apollo_mesh_cli_heartbeat_writes_outbox(tmp_path: Path):
    mesh_dir = tmp_path / "mesh"
    identity_file = mesh_dir / "identity.json"
    _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A2",
        "--fixture",
        "heartbeat",
        "--message",
        "alive",
    )
    outbox = _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A2",
        "--fixture",
        "--json",
        "inbox",
        "--log",
        "outbox",
    )
    payload = json.loads(outbox.stdout)
    assert payload["count"] == 1
    assert payload["events"][0]["kind"] == "node.heartbeat"
