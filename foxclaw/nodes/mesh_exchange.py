"""Private file-drop transport for Apollo Mesh V0."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .mesh import ApolloMeshEvent, ApolloMeshIdentity, dumps_event, event_from_json, verify_mesh_event
from .mesh_store import ApolloMeshStore

EVENTS_DIR = "events"


@dataclass(frozen=True)
class ApolloMeshExchangeResult:
    exchange_dir: str
    events_dir: str
    exported_count: int
    imported_count: int
    skipped_own_count: int
    skipped_existing_count: int
    rejected_count: int


def sync_exchange(
    *,
    identity: ApolloMeshIdentity,
    store: ApolloMeshStore,
    exchange_dir: str | Path,
) -> ApolloMeshExchangeResult:
    """Export local outbox events and import verified peer events from a file drop."""

    root = Path(exchange_dir)
    events_dir = root / EVENTS_DIR
    events_dir.mkdir(parents=True, exist_ok=True)

    exported_count = _export_outbox(store=store, events_dir=events_dir)
    imported_count = 0
    skipped_own_count = 0
    skipped_existing_count = 0
    rejected_count = 0
    inbox_ids = {event.event_id for event in store.read("inbox")}

    for path in sorted(events_dir.glob("*.json")):
        try:
            event = read_event_file(path)
        except (UnicodeError, json.JSONDecodeError, ValueError):
            rejected_count += 1
            continue
        if event.from_node == identity.node_id:
            skipped_own_count += 1
            continue
        if event.event_id in inbox_ids:
            skipped_existing_count += 1
            continue
        if not verify_mesh_event(event, secret=identity.secret):
            rejected_count += 1
            continue
        store.receive(event, secret=identity.secret)
        inbox_ids.add(event.event_id)
        imported_count += 1

    return ApolloMeshExchangeResult(
        exchange_dir=str(root.resolve()),
        events_dir=str(events_dir.resolve()),
        exported_count=exported_count,
        imported_count=imported_count,
        skipped_own_count=skipped_own_count,
        skipped_existing_count=skipped_existing_count,
        rejected_count=rejected_count,
    )


def write_exchange_event(event: ApolloMeshEvent, events_dir: str | Path) -> Path:
    path = Path(events_dir) / event_file_name(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(dumps_event(event), encoding="utf-8")
    return path


def read_event_file(path: str | Path) -> ApolloMeshEvent:
    return event_from_json(json.loads(read_event_text(Path(path))))


def read_event_text(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def event_file_name(event: ApolloMeshEvent) -> str:
    digest = event.event_id.split(":", 1)[-1]
    return f"{_safe_slug(event.from_node)}__{_safe_slug(event.kind)}__{digest}.json"


def _export_outbox(*, store: ApolloMeshStore, events_dir: Path) -> int:
    exported_count = 0
    for event in store.read("outbox"):
        path = events_dir / event_file_name(event)
        if path.exists():
            continue
        write_exchange_event(event, events_dir)
        exported_count += 1
    return exported_count


def _safe_slug(value: Any) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value).strip()).strip("-")
    return slug or "event"
