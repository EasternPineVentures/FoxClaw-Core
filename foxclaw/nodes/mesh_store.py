"""Local append-only Apollo Mesh inbox/outbox logs."""

from __future__ import annotations

import json
from pathlib import Path

from .mesh import ApolloMeshEvent, event_from_json, to_jsonable, verify_mesh_event

VALID_LOGS = frozenset({"inbox", "outbox"})


class ApolloMeshStore:
    def __init__(self, mesh_dir: str | Path) -> None:
        self.mesh_dir = Path(mesh_dir)

    def append(self, log_name: str, event: ApolloMeshEvent) -> Path:
        path = self.log_path(log_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        if event.event_id in {item.event_id for item in self.read(log_name)}:
            return path
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(to_jsonable(event), sort_keys=True, separators=(",", ":")) + "\n")
        return path

    def receive(self, event: ApolloMeshEvent, *, secret: str) -> Path:
        if not verify_mesh_event(event, secret=secret):
            raise ValueError("mesh event signature verification failed")
        return self.append("inbox", event)

    def read(self, log_name: str) -> tuple[ApolloMeshEvent, ...]:
        path = self.log_path(log_name)
        if not path.exists():
            return ()
        events: list[ApolloMeshEvent] = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL event") from exc
            events.append(event_from_json(payload))
        return tuple(events)

    def log_path(self, log_name: str) -> Path:
        if log_name not in VALID_LOGS:
            raise ValueError(f"unknown Apollo Mesh log: {log_name}")
        return self.mesh_dir / f"{log_name}.jsonl"
