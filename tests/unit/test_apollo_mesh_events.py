from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from foxclaw.nodes.mesh import (
    ApolloMeshEvent,
    ApolloMeshIdentity,
    create_mesh_event,
    event_from_json,
    load_or_create_identity,
    to_jsonable,
    verify_mesh_event,
)
from foxclaw.nodes.mesh_store import ApolloMeshStore


SECRET = "test-mesh-secret-" + "1" * 32
NOW = datetime(2026, 6, 18, tzinfo=UTC)


def _identity(node_id: str = "A1") -> ApolloMeshIdentity:
    return ApolloMeshIdentity(
        node_id=node_id,
        key_id="mesh-key:fixture12345678",
        secret=SECRET,
        created_at=NOW,
    )


def test_mesh_event_signs_and_verifies_canonical_payload():
    event = create_mesh_event(
        identity=_identity(),
        kind="node.heartbeat",
        content={"message": "alive"},
        tags=("repo:foxclaw-core",),
        created_at=NOW,
    )

    assert event.protocol == "apollo_mesh_event_v0"
    assert event.event_id.startswith("sha256:")
    assert event.signature.startswith("hmac-sha256:")
    assert event.authority.can_remote_command is False
    assert verify_mesh_event(event, secret=SECRET) is True


def test_mesh_event_tamper_breaks_verification():
    event = create_mesh_event(
        identity=_identity(),
        kind="handoff.note",
        content={"summary": "pull latest", "next_request": "run tests"},
        created_at=NOW,
    )
    payload = to_jsonable(event)
    payload["content"]["summary"] = "different"
    tampered = event_from_json(payload)

    assert verify_mesh_event(tampered, secret=SECRET) is False


def test_mesh_event_rejects_remote_command_or_secret_fields():
    with pytest.raises(ValueError, match="forbidden field"):
        create_mesh_event(
            identity=_identity(),
            kind="runtime.alert",
            content={"command": "restart"},
            created_at=NOW,
        )
    with pytest.raises(ValueError, match="forbidden field"):
        create_mesh_event(
            identity=_identity(),
            kind="context.receipt",
            content={"nested": {"token": "secret"}},
            created_at=NOW,
        )


def test_mesh_store_appends_outbox_and_receives_verified_inbox(tmp_path: Path):
    store = ApolloMeshStore(tmp_path / "mesh")
    event = create_mesh_event(
        identity=_identity(),
        kind="question.ask",
        content={"question": "what changed?"},
        created_at=NOW,
    )

    store.append("outbox", event)
    store.append("outbox", event)
    store.receive(event, secret=SECRET)

    assert len(store.read("outbox")) == 1
    assert len(store.read("inbox")) == 1
    assert store.read("inbox")[0].event_id == event.event_id


def test_load_or_create_identity_keeps_secret_out_of_public_view(tmp_path: Path):
    path = tmp_path / "identity.json"
    identity = load_or_create_identity(path, node_id="A2", secret=SECRET, created_at=NOW)
    loaded = load_or_create_identity(path, node_id="ignored")

    assert loaded.node_id == "A2"
    assert loaded.secret == SECRET
    assert identity.public_view()["secret_loaded"] is True
    assert "secret" not in identity.public_view()
    assert json.loads(path.read_text(encoding="utf-8"))["secret"] == SECRET


def test_mesh_event_cannot_be_rehydrated_with_authority_true():
    event = create_mesh_event(
        identity=_identity(),
        kind="node.heartbeat",
        content={"message": "alive"},
        created_at=NOW,
    )
    payload = to_jsonable(event)
    payload["authority"]["can_submit_order"] = True

    with pytest.raises(ValueError, match="cannot grant authority"):
        event_from_json(payload)
