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
    assert public_identity["node_role"] == "founder_node"
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
    assert event["node_role"] == "founder_node"
    assert event["data_classification"] == "founder_private"
    assert event["redistribution"] == "do_not_export"
    assert event["public_export_allowed"] is False
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


def test_apollo_mesh_cli_receive_accepts_windows_bom_event_file(tmp_path: Path):
    mesh_dir = tmp_path / "mesh"
    identity_file = mesh_dir / "identity.json"
    sent = _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A1",
        "--fixture",
        "--json",
        "heartbeat",
        "--message",
        "alive",
    )

    event_file = tmp_path / "event_with_bom.json"
    event_file.write_text(sent.stdout, encoding="utf-8-sig")
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


def test_apollo_mesh_cli_rekey_and_doctor_do_not_print_secret(tmp_path: Path):
    mesh_dir = tmp_path / "mesh"
    identity_file = mesh_dir / "identity.json"
    secret_file = tmp_path / "founder_mesh_secret.txt"
    secret = "shared-founder-mesh-secret-" + "3" * 32
    secret_file.write_text(secret, encoding="utf-8")

    rekey = _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A2",
        "--json",
        "rekey",
        "--secret-file",
        str(secret_file),
    )
    rekey_payload = json.loads(rekey.stdout)
    assert rekey_payload["rekeyed"] is True
    assert rekey_payload["node_id"] == "A2"
    assert rekey_payload["node_role"] == "founder_node"
    assert rekey_payload["secret_printed"] is False
    assert secret not in rekey.stdout

    doctor = _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A2",
        "--json",
        "doctor",
    )
    doctor_payload = json.loads(doctor.stdout)
    assert doctor_payload["node_id"] == "A2"
    assert doctor_payload["key_id"] == rekey_payload["key_id"]
    assert doctor_payload["identity_exists"] is True
    assert doctor_payload["secret_printed"] is False
    assert doctor_payload["inbox_count"] == 0
    assert doctor_payload["outbox_count"] == 0
    assert secret not in doctor.stdout


def test_apollo_mesh_cli_doctor_does_not_create_identity(tmp_path: Path):
    mesh_dir = tmp_path / "mesh"
    identity_file = mesh_dir / "identity.json"

    doctor = _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A2",
        "--json",
        "doctor",
    )

    doctor_payload = json.loads(doctor.stdout)
    assert doctor_payload["node_id"] == "A2"
    assert doctor_payload["node_role"] == "founder_node"
    assert doctor_payload["key_id"] is None
    assert doctor_payload["identity_exists"] is False
    assert doctor_payload["secret_loaded"] is False
    assert doctor_payload["secret_printed"] is False
    assert not identity_file.exists()
