# Apollo Mesh V0 First Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first local-safe Apollo Mesh slice: signed public-intelligence events, local memory, steward summaries, context packs, and a downloadable testkit scaffold.

**Architecture:** `foxclaw/node` owns the mesh event model, identity, local store, steward, context packs, and CLI. `foxclaw/adapters/nostr` maps FoxClaw events to private Nostr transport using an optional dependency, keeping the engine pure and relay mechanics outside authority. `foxclaw/testkit` packages safe diagnostics and synthetic fixtures for trusted node testers.

**Tech Stack:** Python 3.11, standard library for core node/state logic, `pynostr[websocket-client]==0.7.0` for Nostr-compatible key/signing/relay adapter, pytest, hatchling.

---

## Dependency Contingency

`pynostr==0.7.0` is the first candidate because it is Windows-friendly and exposes direct
Nostr key generation, event signing, and relay manager APIs. It is not architectural glue.
FoxClaw code must isolate it behind `foxclaw/node/identity.py` and `foxclaw/adapters/nostr/*`.

If `pynostr` fails on A1/A2 or produces packaging friction, switch the optional `mesh`
dependency and adapter internals only. The acceptable alternatives are:

- `nostr-sdk==0.44.2`: broader Nostr SDK with Windows wheels, but alpha API.
- A small subprocess wrapper around a reviewed Nostr CLI for signing/publish smoke tests.
- A FoxClaw-native local signer for non-Nostr test events, while keeping the Nostr adapter
  disabled until a stable secp256k1 Schnorr library is selected.

Do not let a library decision leak into `NodeEvent`, `NodeEventStore`, `MeshSteward`,
`context.py`, or `testkit` diagnostics. Those modules must remain transport-agnostic.

## Planning Containment

Keep planning, scratch reasoning, and agent coordination notes inside `docs/superpowers/`.
Do not add scattered migration notes, brainstorming notes, or "temporary" planning files to
runtime folders, engine folders, adapter packages, or the legacy A2 checkout.

The implementation itself stays in a small set of purpose-built modules:

- `foxclaw/node`: FoxClaw-owned event, identity, memory, policy, and CLI code.
- `foxclaw/adapters/nostr`: private relay transport mechanics only.
- `foxclaw/testkit`: safe tester diagnostics and synthetic fixtures only.

## Scope And Stop Conditions

This plan starts after the Apollo Mesh V0 design spec is approved. It deliberately avoids full relay operations, public package publishing, and production node onboarding until A1's newer baseline is pushed and reviewed.

Stop immediately if:

- `git status --short --branch` shows uncommitted A1 work in overlapping files.
- `VERSION` or `docs/a2_migration_context.md` indicates A1's newer baseline landed and this branch needs rebase.
- Any test requires printing private keys, `.env` values, DB contents, or runtime logs.
- A change attempts to give mesh events execution, probability-setting, order, or funds authority.
- A change accepts confidential, non-public, or suspicious market-moving information as
  network intel.

## Public-Intelligence / Market-Integrity Ground Rules

FoxClaw Mesh V0 is a signed public-intelligence and memory network. It must not become a
secret-buying, insider-signal, or auto-trading network.

Accepted `intel.observation` and `intel.receipt` events must carry source provenance and a
shareability attestation. Missing, confidential, suspicious, or non-public intel is
quarantined locally and does not become accepted mesh memory.

Allowed accepted source types:

- `public_url`
- `official_release`
- `licensed_data`
- `own_observation`
- `analysis`

Quarantine-only source/status values:

- `confidential_rejected`
- `suspected_mnpi`
- `unknown`

The Mesh Steward can flag, quarantine, summarize, and ask for human review. It cannot trade,
submit orders, set probabilities, move funds, command another node, or promote quarantined
intel into accepted memory.

## File Structure

- Create `foxclaw/node/__init__.py`: safe exports for mesh primitives.
- Create `foxclaw/node/events.py`: `AuthorityFlags`, `NodeEvent`, validation, canonical JSON, event id.
- Create `foxclaw/node/compliance.py`: public-intelligence provenance, MNPI firewall, quarantine decisions.
- Create `foxclaw/node/identity.py`: local node identity loading/generation using `pynostr`.
- Create `foxclaw/node/store.py`: append-only inbox/outbox JSONL store with duplicate detection.
- Create `foxclaw/node/steward.py`: deterministic advisory manager over accepted events.
- Create `foxclaw/node/context.py`: cited context-pack builder for agents and handoffs.
- Create `foxclaw/node/cli.py`: local CLI for heartbeat, handoff, inbox, steward, context.
- Create `foxclaw/adapters/nostr/__init__.py`: adapter package export.
- Create `foxclaw/adapters/nostr/mapping.py`: FoxClaw `NodeEvent` to private Nostr event mapping.
- Create `foxclaw/adapters/nostr/client.py`: thin publish/subscribe adapter around `pynostr`.
- Create `foxclaw/testkit/__init__.py`: testkit package export.
- Create `foxclaw/testkit/diagnostics.py`: redacted node-test diagnostics.
- Create `foxclaw/testkit/fixtures.py`: synthetic network-intel samples.
- Modify `pyproject.toml`: add `mesh` optional dependency and CLI scripts.
- Add tests under `tests/unit/` and `tests/regression/`.

### Task 1: Package Surfaces And Optional Mesh Dependency

**Files:**
- Modify: `pyproject.toml`
- Create: `foxclaw/node/__init__.py`
- Create: `foxclaw/adapters/nostr/__init__.py`
- Create: `foxclaw/testkit/__init__.py`
- Test: `tests/unit/test_mesh_package_surfaces.py`

- [ ] **Step 1: Write the failing import and metadata tests**

```python
# tests/unit/test_mesh_package_surfaces.py
from __future__ import annotations

from pathlib import Path
import tomllib


def test_node_packages_import_without_side_effects():
    import foxclaw.node as node
    import foxclaw.adapters.nostr as nostr
    import foxclaw.testkit as testkit

    assert node.__all__ == []
    assert nostr.__all__ == []
    assert testkit.__all__ == []


def test_project_exposes_mesh_extra():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    optional_dependencies = pyproject["project"]["optional-dependencies"]
    assert "mesh" in optional_dependencies
    assert "pynostr[websocket-client]==0.7.0" in optional_dependencies["mesh"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_mesh_package_surfaces.py -q`

Expected: FAIL because `foxclaw.node` and `foxclaw.testkit` do not exist and `mesh` extra is not declared.

- [ ] **Step 3: Add package files and metadata**

```python
# foxclaw/node/__init__.py
"""foxclaw.node - signed node-network intel, steward memory, and local mesh tools."""

__all__: list[str] = []
```

```python
# foxclaw/adapters/nostr/__init__.py
"""foxclaw.adapters.nostr - private Nostr transport for Apollo Mesh events."""

__all__: list[str] = []
```

```python
# foxclaw/testkit/__init__.py
"""foxclaw.testkit - safe diagnostics and synthetic fixtures for node testers."""

__all__: list[str] = []
```

Add this to `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = ["pytest", "ruff", "pynostr[websocket-client]==0.7.0"]
mesh = ["pynostr[websocket-client]==0.7.0"]

[project.scripts]
foxclaw-node = "foxclaw.node.cli:main"
foxclaw-testkit = "foxclaw.testkit.diagnostics:main"
```

Keep the existing `dev` tools; the only intentional addition is the mesh signing/relay optional dependency.

- [ ] **Step 4: Run import tests**

Run: `python -m pytest tests/unit/test_mesh_package_surfaces.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml foxclaw/node/__init__.py foxclaw/adapters/nostr/__init__.py foxclaw/testkit/__init__.py tests/unit/test_mesh_package_surfaces.py
git commit -m "feat: add mesh package surfaces"
```

### Task 2: NodeEvent Schema And Authority Rails

**Files:**
- Create: `foxclaw/node/events.py`
- Test: `tests/unit/test_node_events.py`

- [ ] **Step 1: Write failing tests for canonical events**

```python
# tests/unit/test_node_events.py
from __future__ import annotations

import pytest

from foxclaw.node.events import AuthorityFlags, NodeEvent, canonical_json, event_id_for


def test_authority_flags_default_false():
    flags = AuthorityFlags()
    assert flags.as_dict() == {
        "can_submit_orders": False,
        "can_move_funds": False,
        "can_set_probabilities": False,
        "can_execute_remote_actions": False,
    }


def test_node_event_id_is_deterministic():
    event = NodeEvent(
        event_type="node.heartbeat",
        from_node="apollo-2",
        created_at="2026-06-18T00:00:00Z",
        priority="normal",
        summary="Apollo 2 online",
        payload={"version": "0.4.3"},
        references=[],
    )
    assert event.event_id == event_id_for(event.as_dict(include_event_id=False))
    assert event.event_id == NodeEvent.from_dict(event.as_dict()).event_id


def test_node_event_rejects_authority_true():
    with pytest.raises(ValueError, match="authority"):
        NodeEvent(
            event_type="runtime.alert",
            from_node="apollo-2",
            created_at="2026-06-18T00:00:00Z",
            priority="high",
            summary="bad authority",
            payload={},
            references=[],
            authority=AuthorityFlags(can_move_funds=True),
        )


def test_canonical_json_is_stable():
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_node_events.py -q`

Expected: FAIL because `foxclaw.node.events` does not exist.

- [ ] **Step 3: Implement the schema**

```python
# foxclaw/node/events.py
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

ALLOWED_EVENT_TYPES = {
    "node.heartbeat",
    "node.capability_manifest",
    "handoff.note",
    "runtime.alert",
    "intel.observation",
    "intel.receipt",
    "question.ask",
    "question.answer",
    "steward.digest",
    "steward.reminder",
    "steward.escalation",
    "agent.context_pack.created",
    "agent.memory.note",
    "testkit.diagnostic",
    "testkit.join_request",
}

ALLOWED_PRIORITIES = {"low", "normal", "high", "urgent"}


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def event_id_for(value: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuthorityFlags:
    can_submit_orders: bool = False
    can_move_funds: bool = False
    can_set_probabilities: bool = False
    can_execute_remote_actions: bool = False

    def as_dict(self) -> dict[str, bool]:
        return {
            "can_submit_orders": bool(self.can_submit_orders),
            "can_move_funds": bool(self.can_move_funds),
            "can_set_probabilities": bool(self.can_set_probabilities),
            "can_execute_remote_actions": bool(self.can_execute_remote_actions),
        }

    def assert_safe(self) -> None:
        if any(self.as_dict().values()):
            raise ValueError("node mesh authority flags must remain false")


@dataclass(frozen=True)
class NodeEvent:
    event_type: str
    from_node: str
    created_at: str
    priority: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)
    schema_version: int = 1
    event_id: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported node event schema_version")
        if self.event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"unsupported node event type: {self.event_type}")
        if self.priority not in ALLOWED_PRIORITIES:
            raise ValueError(f"unsupported node event priority: {self.priority}")
        if not self.from_node.strip():
            raise ValueError("from_node is required")
        if not self.summary.strip():
            raise ValueError("summary is required")
        self.authority.assert_safe()
        computed = event_id_for(self.as_dict(include_event_id=False))
        object.__setattr__(self, "event_id", self.event_id or computed)
        if self.event_id != computed:
            raise ValueError("event_id does not match canonical event payload")

    def as_dict(self, *, include_event_id: bool = True) -> dict[str, Any]:
        data = {
            "schema_version": self.schema_version,
            "event_type": self.event_type,
            "from_node": self.from_node,
            "created_at": self.created_at,
            "priority": self.priority,
            "summary": self.summary,
            "payload": dict(self.payload),
            "references": list(self.references),
            "authority": self.authority.as_dict(),
        }
        if include_event_id:
            data["event_id"] = self.event_id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NodeEvent":
        auth = AuthorityFlags(**dict(data.get("authority") or {}))
        return cls(
            schema_version=int(data.get("schema_version", 1)),
            event_type=str(data["event_type"]),
            from_node=str(data["from_node"]),
            created_at=str(data["created_at"]),
            priority=str(data["priority"]),
            summary=str(data["summary"]),
            payload=dict(data.get("payload") or {}),
            references=list(data.get("references") or []),
            authority=auth,
            event_id=str(data.get("event_id") or ""),
        )
```

- [ ] **Step 4: Run event tests**

Run: `python -m pytest tests/unit/test_node_events.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add foxclaw/node/events.py tests/unit/test_node_events.py
git commit -m "feat: add node event schema"
```

### Task 3: Public-Intelligence Compliance Firewall

**Files:**
- Create: `foxclaw/node/compliance.py`
- Test: `tests/unit/test_mesh_compliance.py`

- [ ] **Step 1: Write failing tests for provenance, attestation, and MNPI quarantine**

```python
# tests/unit/test_mesh_compliance.py
from __future__ import annotations

from foxclaw.node.compliance import review_public_intel
from foxclaw.node.events import NodeEvent


def make_intel(payload: dict[str, object]) -> NodeEvent:
    return NodeEvent(
        event_type="intel.observation",
        from_node="apollo-2",
        created_at="2026-06-18T00:00:00Z",
        priority="normal",
        summary="public-intel test event",
        payload=payload,
        references=[],
    )


def test_public_url_with_attestation_is_accepted():
    event = make_intel(
        {
            "source_type": "public_url",
            "evidence": {"url": "https://example.com/official-release"},
            "rights_attestation": {"can_share": True, "not_confidential": True},
            "mnpi_status": "not_mnpi",
        }
    )
    review = review_public_intel(event)
    assert review.status == "accepted"
    assert review.reason == "public_intel_provenance_passed"


def test_missing_attestation_is_quarantined():
    event = make_intel(
        {
            "source_type": "official_release",
            "evidence": {"url": "https://example.com/filing"},
            "mnpi_status": "not_mnpi",
        }
    )
    review = review_public_intel(event)
    assert review.status == "quarantined"
    assert review.reason == "missing_shareability_attestation"


def test_suspected_mnpi_is_quarantined():
    event = make_intel(
        {
            "source_type": "confidential_rejected",
            "evidence": {"note": "claimed private source"},
            "rights_attestation": {"can_share": False, "not_confidential": False},
            "mnpi_status": "suspected_mnpi",
        }
    )
    review = review_public_intel(event)
    assert review.status == "quarantined"
    assert review.reason == "suspected_or_non_public_market_intel"


def test_non_intel_event_is_not_blocked_by_intel_firewall():
    heartbeat = NodeEvent(
        event_type="node.heartbeat",
        from_node="apollo-2",
        created_at="2026-06-18T00:00:00Z",
        priority="normal",
        summary="Apollo 2 online",
        payload={},
        references=[],
    )
    review = review_public_intel(heartbeat)
    assert review.status == "accepted"
    assert review.reason == "not_public_intel_event"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_mesh_compliance.py -q`

Expected: FAIL because `foxclaw.node.compliance` does not exist.

- [ ] **Step 3: Implement the compliance firewall**

```python
# foxclaw/node/compliance.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .events import NodeEvent

PUBLIC_INTEL_EVENT_TYPES = {"intel.observation", "intel.receipt"}

ACCEPTED_SOURCE_TYPES = {
    "public_url",
    "official_release",
    "licensed_data",
    "own_observation",
    "analysis",
}

QUARANTINE_SOURCE_TYPES = {"confidential_rejected"}
QUARANTINE_MNPI_STATUSES = {"suspected_mnpi", "unknown"}


@dataclass(frozen=True)
class ComplianceReview:
    status: str
    reason: str
    policy: str = "public_intel_v1"

    def as_dict(self) -> dict[str, str]:
        return {"status": self.status, "reason": self.reason, "policy": self.policy}


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def review_public_intel(event: NodeEvent) -> ComplianceReview:
    if event.event_type not in PUBLIC_INTEL_EVENT_TYPES:
        return ComplianceReview(status="accepted", reason="not_public_intel_event")

    payload = event.payload
    source_type = str(payload.get("source_type", "")).strip()
    mnpi_status = str(payload.get("mnpi_status", "")).strip()
    evidence = _as_mapping(payload.get("evidence"))
    attestation = _as_mapping(payload.get("rights_attestation"))

    if source_type in QUARANTINE_SOURCE_TYPES or mnpi_status in QUARANTINE_MNPI_STATUSES:
        return ComplianceReview(
            status="quarantined",
            reason="suspected_or_non_public_market_intel",
        )

    if source_type not in ACCEPTED_SOURCE_TYPES:
        return ComplianceReview(status="quarantined", reason="unsupported_source_type")

    if mnpi_status != "not_mnpi":
        return ComplianceReview(
            status="quarantined",
            reason="missing_or_invalid_mnpi_status",
        )

    if not attestation.get("can_share") or not attestation.get("not_confidential"):
        return ComplianceReview(
            status="quarantined",
            reason="missing_shareability_attestation",
        )

    if source_type in {"public_url", "official_release"} and not evidence.get("url"):
        return ComplianceReview(status="quarantined", reason="missing_public_evidence_url")

    if source_type in {"licensed_data", "own_observation", "analysis"} and not evidence:
        return ComplianceReview(status="quarantined", reason="missing_evidence")

    return ComplianceReview(status="accepted", reason="public_intel_provenance_passed")
```

- [ ] **Step 4: Run compliance tests**

Run: `python -m pytest tests/unit/test_mesh_compliance.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add foxclaw/node/compliance.py tests/unit/test_mesh_compliance.py
git commit -m "feat: add public intel compliance firewall"
```

### Task 4: Test Identity And Nostr Mapping

**Files:**
- Create: `foxclaw/node/identity.py`
- Create: `foxclaw/adapters/nostr/mapping.py`
- Test: `tests/unit/test_node_identity_nostr_mapping.py`

- [ ] **Step 1: Write failing tests for test-only identities and Nostr mapping**

```python
# tests/unit/test_node_identity_nostr_mapping.py
from __future__ import annotations

import json

from foxclaw.adapters.nostr.mapping import FOXCLAW_MESH_KIND, node_event_to_nostr_event
from foxclaw.node.events import NodeEvent
from foxclaw.node.identity import generate_test_identity


def test_generate_test_identity_is_marked_test_only():
    identity = generate_test_identity("tester-1")
    assert identity.node_id == "tester-1"
    assert identity.public_key_hex
    assert identity.private_key_hex
    assert identity.test_only is True


def test_node_event_maps_to_signed_nostr_event():
    identity = generate_test_identity("tester-1")
    event = NodeEvent(
        event_type="intel.observation",
        from_node="tester-1",
        created_at="2026-06-18T00:00:00Z",
        priority="normal",
        summary="synthetic test intel",
        payload={"fixture": True},
        references=[],
    )
    nostr_event = node_event_to_nostr_event(event, identity)
    as_dict = nostr_event.to_dict()
    assert as_dict["kind"] == FOXCLAW_MESH_KIND
    assert as_dict["pubkey"] == identity.public_key_hex
    assert as_dict["sig"]
    assert ["fctype", "intel.observation"] in as_dict["tags"]
    assert ["node", "tester-1"] in as_dict["tags"]
    assert json.loads(as_dict["content"])["event_id"] == event.event_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_node_identity_nostr_mapping.py -q`

Expected: FAIL because identity and mapping modules do not exist.

- [ ] **Step 3: Implement identity and mapping**

```python
# foxclaw/node/identity.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pynostr.key import PrivateKey


@dataclass(frozen=True)
class NodeIdentity:
    node_id: str
    public_key_hex: str
    private_key_hex: str
    test_only: bool = True


def generate_test_identity(node_id: str) -> NodeIdentity:
    key = PrivateKey()
    return NodeIdentity(
        node_id=str(node_id),
        public_key_hex=key.public_key.hex(),
        private_key_hex=key.hex(),
        test_only=True,
    )


def write_identity(identity: NodeIdentity, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join([
            f"node_id={identity.node_id}",
            f"public_key_hex={identity.public_key_hex}",
            f"private_key_hex={identity.private_key_hex}",
            f"test_only={str(identity.test_only).lower()}",
            "",
        ]),
        encoding="utf-8",
    )
```

```python
# foxclaw/adapters/nostr/mapping.py
from __future__ import annotations

import json

from pynostr.event import Event

from foxclaw.node.events import NodeEvent
from foxclaw.node.identity import NodeIdentity

FOXCLAW_MESH_KIND = 9030


def node_event_to_nostr_event(event: NodeEvent, identity: NodeIdentity) -> Event:
    if event.from_node != identity.node_id:
        raise ValueError("node event sender does not match signing identity")
    nostr_event = Event(
        content=json.dumps(event.as_dict(), sort_keys=True, separators=(",", ":")),
        kind=FOXCLAW_MESH_KIND,
        tags=[
            ["t", "foxclaw-mesh"],
            ["schema", str(event.schema_version)],
            ["fctype", event.event_type],
            ["node", event.from_node],
            ["priority", event.priority],
        ],
    )
    for ref in event.references:
        nostr_event.add_event_ref(str(ref).removeprefix("sha256:"))
    nostr_event.sign(identity.private_key_hex)
    return nostr_event
```

- [ ] **Step 4: Run mapping tests**

Run: `python -m pytest tests/unit/test_node_identity_nostr_mapping.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add foxclaw/node/identity.py foxclaw/adapters/nostr/mapping.py tests/unit/test_node_identity_nostr_mapping.py
git commit -m "feat: add test node identity and nostr mapping"
```

### Task 5: Local Append-Only Event Store

**Files:**
- Create: `foxclaw/node/store.py`
- Test: `tests/unit/test_node_event_store.py`

- [ ] **Step 1: Write failing store tests**

```python
# tests/unit/test_node_event_store.py
from __future__ import annotations

from foxclaw.node.events import NodeEvent
from foxclaw.node.store import NodeEventStore


def make_event(summary: str = "online") -> NodeEvent:
    return NodeEvent(
        event_type="node.heartbeat",
        from_node="apollo-2",
        created_at="2026-06-18T00:00:00Z",
        priority="normal",
        summary=summary,
        payload={},
        references=[],
    )


def test_outbox_append_and_dedupe(tmp_path):
    store = NodeEventStore(tmp_path)
    event = make_event()
    assert store.append_outbox(event)["status"] == "accepted"
    assert store.append_outbox(event)["status"] == "duplicate"
    assert len(store.outbox()) == 1


def test_inbox_quarantine_status_is_retained(tmp_path):
    store = NodeEventStore(tmp_path)
    event = make_event("remote online")
    store.append_inbox(event, status="quarantined", reason="unknown pubkey")
    row = store.inbox()[0]
    assert row["status"] == "quarantined"
    assert row["reason"] == "unknown pubkey"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_node_event_store.py -q`

Expected: FAIL because `NodeEventStore` does not exist.

- [ ] **Step 3: Implement JSONL store**

```python
# foxclaw/node/store.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .events import NodeEvent


class NodeEventStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.inbox_path = self.root / "inbox.jsonl"
        self.outbox_path = self.root / "outbox.jsonl"

    def _read(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _append(self, path: Path, record: dict[str, Any]) -> dict[str, Any]:
        existing = self._read(path)
        event_id = record["event"]["event_id"]
        if any(row["event"]["event_id"] == event_id for row in existing):
            return {"status": "duplicate", "event_id": event_id}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        return {"status": "accepted", "event_id": event_id}

    def append_outbox(self, event: NodeEvent) -> dict[str, Any]:
        return self._append(self.outbox_path, {"status": "accepted", "event": event.as_dict()})

    def append_inbox(
        self,
        event: NodeEvent,
        *,
        status: str = "accepted",
        reason: str = "",
    ) -> dict[str, Any]:
        return self._append(
            self.inbox_path,
            {"status": status, "reason": reason, "event": event.as_dict()},
        )

    def inbox(self) -> list[dict[str, Any]]:
        return self._read(self.inbox_path)

    def outbox(self) -> list[dict[str, Any]]:
        return self._read(self.outbox_path)
```

- [ ] **Step 4: Run store tests**

Run: `python -m pytest tests/unit/test_node_event_store.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add foxclaw/node/store.py tests/unit/test_node_event_store.py
git commit -m "feat: add local node event store"
```

### Task 6: Steward And Context Packs

**Files:**
- Create: `foxclaw/node/steward.py`
- Create: `foxclaw/node/context.py`
- Test: `tests/unit/test_mesh_steward_context.py`

- [ ] **Step 1: Write failing steward and context tests**

```python
# tests/unit/test_mesh_steward_context.py
from __future__ import annotations

from foxclaw.node.context import build_context_pack
from foxclaw.node.events import NodeEvent
from foxclaw.node.steward import MeshSteward


def event(event_type: str, summary: str, refs: list[str] | None = None) -> NodeEvent:
    return NodeEvent(
        event_type=event_type,
        from_node="apollo-2",
        created_at="2026-06-18T00:00:00Z",
        priority="normal",
        summary=summary,
        payload={},
        references=refs or [],
    )


def test_steward_digest_cites_source_event_ids():
    source = event("handoff.note", "finish mesh plan")
    digest = MeshSteward("apollo-2").digest([source])
    assert digest.event_type == "steward.digest"
    assert source.event_id in digest.references
    assert "finish mesh plan" in digest.summary


def test_steward_reminder_for_unanswered_question():
    question = event("question.ask", "what relay URL should testers use?")
    reminders = MeshSteward("apollo-2").reminders([question])
    assert len(reminders) == 1
    assert reminders[0].event_type == "steward.reminder"
    assert question.event_id in reminders[0].references


def test_context_pack_includes_constraints_and_citations():
    source = event("runtime.alert", "old A2 runtime still active")
    pack = build_context_pack(
        purpose="A1/A2 mesh implementation",
        events=[source],
        constraints=["no remote execution"],
        allowed_actions=["write tests", "write local-only code"],
    )
    assert pack["purpose"] == "A1/A2 mesh implementation"
    assert source.event_id in pack["event_ids"]
    assert "no remote execution" in pack["constraints"]
    assert "write tests" in pack["allowed_actions"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_mesh_steward_context.py -q`

Expected: FAIL because `steward` and `context` modules do not exist.

- [ ] **Step 3: Implement deterministic steward and context pack builder**

```python
# foxclaw/node/steward.py
from __future__ import annotations

from .events import NodeEvent


class MeshSteward:
    def __init__(self, node_id: str) -> None:
        self.node_id = node_id

    def digest(self, events: list[NodeEvent]) -> NodeEvent:
        summaries = [event.summary for event in events[:5]]
        summary = "; ".join(summaries) if summaries else "No accepted mesh events yet"
        return NodeEvent(
            event_type="steward.digest",
            from_node=self.node_id,
            created_at="2026-06-18T00:00:00Z",
            priority="normal",
            summary=summary,
            payload={"source_count": len(events)},
            references=[event.event_id for event in events],
        )

    def reminders(self, events: list[NodeEvent]) -> list[NodeEvent]:
        answered = {ref for event in events if event.event_type == "question.answer" for ref in event.references}
        reminders: list[NodeEvent] = []
        for source in events:
            if source.event_type == "question.ask" and source.event_id not in answered:
                reminders.append(
                    NodeEvent(
                        event_type="steward.reminder",
                        from_node=self.node_id,
                        created_at="2026-06-18T00:00:00Z",
                        priority="normal",
                        summary=f"Unanswered question: {source.summary}",
                        payload={"reason": "unanswered_question"},
                        references=[source.event_id],
                    )
                )
        return reminders
```

```python
# foxclaw/node/context.py
from __future__ import annotations

from typing import Any

from .events import NodeEvent


def build_context_pack(
    *,
    purpose: str,
    events: list[NodeEvent],
    constraints: list[str],
    allowed_actions: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "purpose": purpose,
        "event_ids": [event.event_id for event in events],
        "summaries": [event.summary for event in events],
        "constraints": list(constraints),
        "allowed_actions": list(allowed_actions),
        "authority": {
            "can_submit_orders": False,
            "can_move_funds": False,
            "can_set_probabilities": False,
            "can_execute_remote_actions": False,
        },
    }
```

- [ ] **Step 4: Run steward/context tests**

Run: `python -m pytest tests/unit/test_mesh_steward_context.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add foxclaw/node/steward.py foxclaw/node/context.py tests/unit/test_mesh_steward_context.py
git commit -m "feat: add mesh steward and context packs"
```

### Task 7: Testkit Diagnostics And Internal Wheel Guard

**Files:**
- Create: `foxclaw/testkit/diagnostics.py`
- Create: `foxclaw/testkit/fixtures.py`
- Test: `tests/unit/test_node_testkit.py`
- Test: `tests/regression/test_node_testkit_package_guard.py`

- [ ] **Step 1: Write failing testkit tests**

```python
# tests/unit/test_node_testkit.py
from __future__ import annotations

from foxclaw.testkit.diagnostics import redact_value, run_diagnostics
from foxclaw.testkit.fixtures import synthetic_observation


def test_redact_value_hides_paths_and_secret_shapes():
    assert redact_value("C:/Users/fox1i/Desktop/FoxClaw/.env") == "<redacted-path>"
    assert redact_value("gho_abcdefghijklmnopqrstuvwxyz") == "<redacted-secret>"


def test_synthetic_observation_is_test_only():
    event = synthetic_observation("tester-1")
    assert event.event_type == "intel.observation"
    assert event.payload["test_fixture"] is True
    assert event.payload["source_type"] == "analysis"
    assert event.payload["mnpi_status"] == "not_mnpi"


def test_run_diagnostics_is_redacted(tmp_path):
    report = run_diagnostics(root=tmp_path, node_id="tester-1")
    assert report["node_id"] == "tester-1"
    assert report["authority"]["can_move_funds"] is False
```

```python
# tests/regression/test_node_testkit_package_guard.py
from __future__ import annotations

import subprocess
import sys


def test_package_guard_excludes_private_runtime_files():
    result = subprocess.run(
        [sys.executable, "-m", "foxclaw.testkit.diagnostics", "--package-guard"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "package guard passed" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_node_testkit.py tests/regression/test_node_testkit_package_guard.py -q`

Expected: FAIL because testkit modules do not exist.

- [ ] **Step 3: Implement diagnostics and synthetic fixture**

```python
# foxclaw/testkit/fixtures.py
from __future__ import annotations

from foxclaw.node.events import NodeEvent


def synthetic_observation(node_id: str) -> NodeEvent:
    return NodeEvent(
        event_type="intel.observation",
        from_node=node_id,
        created_at="2026-06-18T00:00:00Z",
        priority="normal",
        summary="Synthetic test intel fixture",
        payload={
            "test_fixture": True,
            "source_type": "analysis",
            "evidence": {"note": "synthetic fixture generated by foxclaw.testkit"},
            "rights_attestation": {"can_share": True, "not_confidential": True},
            "mnpi_status": "not_mnpi",
        },
        references=[],
    )
```

```python
# foxclaw/testkit/diagnostics.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any


PRIVATE_PATTERNS = (".env", ".db", ".db-wal", ".db-shm", "runtime_logs")
SECRET_PREFIXES = ("gho_", "sk-", "xoxb-", "nsec1")


def redact_value(value: str) -> str:
    text = str(value)
    if any(pattern in text for pattern in PRIVATE_PATTERNS):
        return "<redacted-path>"
    if any(text.startswith(prefix) for prefix in SECRET_PREFIXES):
        return "<redacted-secret>"
    return text


def run_diagnostics(*, root: str | Path, node_id: str) -> dict[str, Any]:
    base = Path(root)
    return {
        "schema_version": 1,
        "node_id": node_id,
        "root": redact_value(str(base)),
        "can_write_runtime": base.exists() and base.is_dir(),
        "authority": {
            "can_submit_orders": False,
            "can_move_funds": False,
            "can_set_probabilities": False,
            "can_execute_remote_actions": False,
        },
    }


def package_guard() -> list[str]:
    blocked: list[str] = []
    for pattern in PRIVATE_PATTERNS:
        blocked.extend(str(path) for path in Path(".").glob(f"**/*{pattern}*"))
    return [path for path in blocked if ".git" not in path and "__pycache__" not in path]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-guard", action="store_true")
    args = parser.parse_args(argv)
    if args.package_guard:
        blocked = package_guard()
        if blocked:
            print("package guard failed")
            return 1
        print("package guard passed")
        return 0
    print(run_diagnostics(root=Path.cwd(), node_id="tester"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run testkit tests**

Run: `python -m pytest tests/unit/test_node_testkit.py tests/regression/test_node_testkit_package_guard.py -q`

Expected: PASS.

- [ ] **Step 5: Build an internal wheel**

Run: `python -m pip install build && python -m build --wheel`

Expected: PASS and a wheel under `dist/`. Do not commit `dist/`.

- [ ] **Step 6: Commit**

```bash
git add foxclaw/testkit/diagnostics.py foxclaw/testkit/fixtures.py tests/unit/test_node_testkit.py tests/regression/test_node_testkit_package_guard.py
git commit -m "feat: add node testkit diagnostics"
```

### Task 8: Full Verification

**Files:**
- Modify only files already introduced by Tasks 1-7 if verification fails.

- [ ] **Step 1: Run focused mesh tests**

Run: `python -m pytest tests/unit/test_mesh_package_surfaces.py tests/unit/test_node_events.py tests/unit/test_mesh_compliance.py tests/unit/test_node_identity_nostr_mapping.py tests/unit/test_node_event_store.py tests/unit/test_mesh_steward_context.py tests/unit/test_node_testkit.py tests/regression/test_node_testkit_package_guard.py -q`

Expected: PASS.

- [ ] **Step 2: Run full suite**

Run: `python -m pytest -q`

Expected: PASS with the existing skip count preserved unless a dependency-specific skip is intentionally added.

- [ ] **Step 3: Run invariant guard**

Run: `python tools/check_invariants.py`

Expected: all structural invariants hold.

- [ ] **Step 4: Run diff hygiene**

Run: `git diff --check`

Expected: no output.

- [ ] **Step 5: Commit verification notes if docs changed**

If no docs changed during verification, do not create a commit. If a verification note is added to the plan or design, commit it explicitly:

```bash
git add docs/superpowers/plans/2026-06-18-apollo-mesh-v0-first-slice.md
git commit -m "docs: record apollo mesh verification notes"
```

## Execution Handoff

Plan execution should start only after A1 either pushes the `0.4.3+` baseline or explicitly approves building this branch from the current `0.1.4` remote baseline. Use subagent-driven development if possible, with one task per subagent and review between tasks.
