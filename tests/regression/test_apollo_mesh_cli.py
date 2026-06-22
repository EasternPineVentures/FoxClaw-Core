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


def test_apollo_mesh_cli_sync_exports_and_imports_peer_events(tmp_path: Path):
    exchange_dir = tmp_path / "exchange"
    a1_mesh = tmp_path / "a1_mesh"
    a2_mesh = tmp_path / "a2_mesh"
    _run(
        "--mesh-dir",
        str(a1_mesh),
        "--identity-file",
        str(a1_mesh / "identity.json"),
        "--node-id",
        "A1",
        "--fixture",
        "--json",
        "heartbeat",
        "--message",
        "A1 ready",
    )

    a1_sync = _run(
        "--mesh-dir",
        str(a1_mesh),
        "--identity-file",
        str(a1_mesh / "identity.json"),
        "--node-id",
        "A1",
        "--fixture",
        "--exchange-dir",
        str(exchange_dir),
        "--json",
        "sync",
    )
    a1_payload = json.loads(a1_sync.stdout)
    assert a1_payload["exported_count"] == 1
    assert a1_payload["imported_count"] == 0
    assert a1_payload["skipped_own_count"] == 1
    assert a1_payload["secret_printed"] is False

    a2_sync = _run(
        "--mesh-dir",
        str(a2_mesh),
        "--identity-file",
        str(a2_mesh / "identity.json"),
        "--node-id",
        "A2",
        "--fixture",
        "--exchange-dir",
        str(exchange_dir),
        "--json",
        "sync",
    )
    a2_payload = json.loads(a2_sync.stdout)
    assert a2_payload["exported_count"] == 0
    assert a2_payload["imported_count"] == 1
    assert a2_payload["skipped_own_count"] == 0
    assert a2_payload["secret_printed"] is False

    inbox = _run(
        "--mesh-dir",
        str(a2_mesh),
        "--identity-file",
        str(a2_mesh / "identity.json"),
        "--node-id",
        "A2",
        "--fixture",
        "--json",
        "inbox",
    )
    inbox_payload = json.loads(inbox.stdout)
    assert inbox_payload["count"] == 1
    assert inbox_payload["events"][0]["from_node"] == "A1"
    assert inbox_payload["events"][0]["content"]["message"] == "A1 ready"


def test_apollo_mesh_cli_pulse_creates_heartbeat_and_syncs(tmp_path: Path):
    exchange_dir = tmp_path / "exchange"
    a1_mesh = tmp_path / "a1_mesh"
    a2_mesh = tmp_path / "a2_mesh"

    pulse = _run(
        "--mesh-dir",
        str(a2_mesh),
        "--identity-file",
        str(a2_mesh / "identity.json"),
        "--node-id",
        "A2",
        "--fixture",
        "--exchange-dir",
        str(exchange_dir),
        "--json",
        "pulse",
        "--message",
        "A2 pulse",
    )
    pulse_payload = json.loads(pulse.stdout)
    assert pulse_payload["pulse_kind"] == "node.heartbeat"
    assert pulse_payload["sync"]["exported_count"] == 1
    assert pulse_payload["sync"]["skipped_own_count"] == 1
    assert pulse_payload["secret_printed"] is False

    a1_sync = _run(
        "--mesh-dir",
        str(a1_mesh),
        "--identity-file",
        str(a1_mesh / "identity.json"),
        "--node-id",
        "A1",
        "--fixture",
        "--exchange-dir",
        str(exchange_dir),
        "--json",
        "sync",
    )
    a1_payload = json.loads(a1_sync.stdout)
    assert a1_payload["imported_count"] == 1

    inbox = _run(
        "--mesh-dir",
        str(a1_mesh),
        "--identity-file",
        str(a1_mesh / "identity.json"),
        "--node-id",
        "A1",
        "--fixture",
        "--json",
        "inbox",
    )
    inbox_payload = json.loads(inbox.stdout)
    assert inbox_payload["count"] == 1
    assert inbox_payload["events"][0]["from_node"] == "A2"
    assert inbox_payload["events"][0]["content"]["message"] == "A2 pulse"


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


def test_apollo_mesh_cli_courier_verbs_write_private_outbox(tmp_path: Path):
    mesh_dir = tmp_path / "mesh"
    identity_file = mesh_dir / "identity.json"

    commands = (
        (
            "manifest",
            "--capability",
            "branch-sync",
            "--status",
            "available",
            "--note",
            "safe ff-only branch positioning",
        ),
        (
            "ask",
            "--to-node",
            "A2",
            "--question",
            "which branch is parser parity using?",
            "--priority",
            "high",
            "--context-ref",
            "feature/parser-compat-v0",
        ),
        (
            "answer",
            "--to-node",
            "A1",
            "--question-event-id",
            "sha256:question",
            "--answer",
            "A2 is on feature/parser-compat-v0",
        ),
        (
            "alert",
            "--severity",
            "warning",
            "--message",
            "A2 has a dirty tree",
            "--source",
            "branch-sync",
        ),
        (
            "receipt",
            "--title",
            "A2 branch aligned",
            "--summary",
            "feature branch is tracking origin",
            "--status",
            "ready",
        ),
    )

    for command in commands:
        _run(
            "--mesh-dir",
            str(mesh_dir),
            "--identity-file",
            str(identity_file),
            "--node-id",
            "A1",
            "--fixture",
            "--json",
            *command,
        )

    outbox = _run(
        "--mesh-dir",
        str(mesh_dir),
        "--identity-file",
        str(identity_file),
        "--node-id",
        "A1",
        "--fixture",
        "--json",
        "inbox",
        "--log",
        "outbox",
    )
    payload = json.loads(outbox.stdout)

    assert payload["count"] == 5
    assert [event["kind"] for event in payload["events"]] == [
        "node.capability_manifest",
        "question.ask",
        "question.answer",
        "runtime.alert",
        "context.receipt",
    ]
    assert all(event["data_classification"] == "founder_private" for event in payload["events"])
    assert all(event["public_export_allowed"] is False for event in payload["events"])
    assert all(event["authority"]["can_remote_command"] is False for event in payload["events"])


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
