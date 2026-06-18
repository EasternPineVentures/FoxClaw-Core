#!/usr/bin/env python3
"""Apollo Mesh V0 local signed node-event CLI."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.nodes.mesh import (  # noqa: E402
    ApolloMeshIdentity,
    create_mesh_event,
    dumps_event,
    event_from_json,
    load_or_create_identity,
    to_jsonable,
    verify_mesh_event,
)
from foxclaw.nodes.mesh_store import ApolloMeshStore  # noqa: E402

DEFAULT_MESH_DIR = REPO / "data" / "apollo_mesh"
FIXTURE_SECRET = "fixture-mesh-secret-" + "0" * 32
FIXTURE_TIME = datetime(2026, 6, 18, 0, 0, tzinfo=UTC)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesh-dir", default=str(DEFAULT_MESH_DIR))
    parser.add_argument("--identity-file")
    parser.add_argument("--node-id", default="apollo")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    heartbeat = sub.add_parser("heartbeat")
    heartbeat.add_argument("--message", default="alive")
    heartbeat.add_argument("--tag", action="append", default=[])

    handoff = sub.add_parser("handoff")
    handoff.add_argument("--to-node", required=True)
    handoff.add_argument("--summary", required=True)
    handoff.add_argument("--next-request", required=True)
    handoff.add_argument("--current-slice", default="handoff")
    handoff.add_argument("--tag", action="append", default=[])

    receive = sub.add_parser("receive")
    receive.add_argument("--event-file", required=True)

    inbox = sub.add_parser("inbox")
    inbox.add_argument("--log", choices=("inbox", "outbox"), default="inbox")

    args = parser.parse_args(argv)
    mesh_dir = Path(args.mesh_dir)
    identity = _identity(args)
    store = ApolloMeshStore(mesh_dir)

    if args.command == "init":
        return _emit(identity.public_view(), json_mode=args.json)
    if args.command == "heartbeat":
        event = create_mesh_event(
            identity=identity,
            kind="node.heartbeat",
            content={"message": args.message},
            tags=tuple(args.tag),
            created_at=FIXTURE_TIME if args.fixture else None,
        )
        store.append("outbox", event)
        return _emit(event, json_mode=args.json)
    if args.command == "handoff":
        event = create_mesh_event(
            identity=identity,
            kind="handoff.note",
            content={
                "to_node": args.to_node,
                "summary": args.summary,
                "current_slice": args.current_slice,
                "next_request": args.next_request,
            },
            tags=tuple([f"to:{args.to_node}", *args.tag]),
            created_at=FIXTURE_TIME if args.fixture else None,
        )
        store.append("outbox", event)
        return _emit(event, json_mode=args.json)
    if args.command == "receive":
        payload = json.loads(Path(args.event_file).read_text(encoding="utf-8"))
        event = event_from_json(payload)
        verified = verify_mesh_event(event, secret=identity.secret)
        if not verified:
            raise SystemExit("mesh event signature verification failed")
        store.receive(event, secret=identity.secret)
        return _emit({"received": True, "event_id": event.event_id}, json_mode=args.json)
    if args.command == "inbox":
        events = store.read(args.log)
        return _emit({"log": args.log, "count": len(events), "events": list(events)}, json_mode=args.json)
    raise SystemExit(f"unsupported command: {args.command}")


def _identity(args: argparse.Namespace) -> ApolloMeshIdentity:
    path = Path(args.identity_file) if args.identity_file else Path(args.mesh_dir) / "identity.json"
    return load_or_create_identity(
        path,
        node_id=args.node_id,
        secret=FIXTURE_SECRET if args.fixture else None,
        created_at=FIXTURE_TIME if args.fixture else None,
    )


def _emit(value: Any, *, json_mode: bool) -> int:
    if json_mode:
        if hasattr(value, "event_id"):
            print(dumps_event(value), end="")
        else:
            print(json.dumps(to_jsonable(value), indent=2, sort_keys=True))
        return 0
    if hasattr(value, "event_id"):
        print(f"event_id: {value.event_id}")
        print(f"kind: {value.kind}")
        print(f"from_node: {value.from_node}")
        print(f"signature: verified-local")
        print("authority: false")
        return 0
    for key, item in to_jsonable(value).items():
        print(f"{key}: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
