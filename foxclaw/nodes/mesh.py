"""Apollo Mesh V0 signed node events.

V0 uses a private HMAC-SHA256 mesh secret from a gitignored identity file or
`FOXCLAW_MESH_SECRET`. Public-key/Nostr transport can be added as an adapter after this
local contract is stable.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

MESH_PROTOCOL = "apollo_mesh_event_v0"
MESH_SCHEMA_VERSION = 1
MESH_SECRET_ENV = "FOXCLAW_MESH_SECRET"
SIGNATURE_PREFIX = "hmac-sha256:"
FOUNDER_NODE_ROLE = "founder_node"
FOUNDER_PRIVATE = "founder_private"
DO_NOT_EXPORT = "do_not_export"

ALLOWED_NODE_ROLES = frozenset({FOUNDER_NODE_ROLE})
ALLOWED_DATA_CLASSIFICATIONS = frozenset({FOUNDER_PRIVATE})
ALLOWED_REDISTRIBUTION = frozenset({DO_NOT_EXPORT, "founder_mesh_only"})

ALLOWED_EVENT_KINDS = frozenset(
    {
        "node.heartbeat",
        "node.capability_manifest",
        "handoff.note",
        "runtime.alert",
        "context.receipt",
        "question.ask",
        "question.answer",
        "forecast.evidence",
    }
)

FORBIDDEN_CONTENT_FIELDS = frozenset(
    {
        "account_id",
        "api_key",
        "can_move_funds",
        "can_set_probability",
        "can_submit_order",
        "command",
        "execute",
        "live_execution_allowed",
        "live_order_id",
        "move_funds",
        "password",
        "private_key",
        "secret",
        "submit_order",
        "token",
    }
)


@dataclass(frozen=True)
class MeshAuthorityLocks:
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False
    can_set_probability: bool = False
    can_remote_command: bool = False

    def __post_init__(self) -> None:
        if any(
            (
                self.can_submit_order,
                self.can_move_funds,
                self.live_execution_allowed,
                self.can_set_probability,
                self.can_remote_command,
            )
        ):
            raise ValueError("Apollo Mesh events cannot grant authority")


@dataclass(frozen=True)
class ApolloMeshIdentity:
    node_id: str
    key_id: str
    secret: str
    created_at: datetime
    node_role: str = FOUNDER_NODE_ROLE

    def __post_init__(self) -> None:
        if not _text(self.node_id):
            raise ValueError("node_id is required")
        if not self.key_id.startswith("mesh-key:"):
            raise ValueError("key_id must be mesh-key-prefixed")
        if len(self.secret) < 32:
            raise ValueError("mesh secret is too short")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        if self.node_role not in ALLOWED_NODE_ROLES:
            raise ValueError("Apollo Mesh V0 is founder-node only")

    def public_view(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_role": self.node_role,
            "key_id": self.key_id,
            "created_at": _iso(self.created_at),
            "secret_loaded": True,
        }


@dataclass(frozen=True)
class ApolloMeshEvent:
    protocol: str
    schema_version: int
    event_id: str
    from_node: str
    node_role: str
    created_at: datetime
    kind: str
    tags: tuple[str, ...]
    content: Mapping[str, Any]
    data_classification: str
    redistribution: str
    public_export_allowed: bool
    prev_hash: str | None
    signer_key_id: str
    signature: str
    authority: MeshAuthorityLocks

    def __post_init__(self) -> None:
        if self.protocol != MESH_PROTOCOL:
            raise ValueError(f"unsupported mesh protocol: {self.protocol}")
        if self.schema_version != MESH_SCHEMA_VERSION:
            raise ValueError(f"unsupported mesh schema version: {self.schema_version}")
        if not self.event_id.startswith("sha256:"):
            raise ValueError("event_id must be sha256-prefixed")
        if not _text(self.from_node):
            raise ValueError("from_node is required")
        if self.node_role not in ALLOWED_NODE_ROLES:
            raise ValueError("Apollo Mesh V0 accepts founder-node events only")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        if self.kind not in ALLOWED_EVENT_KINDS:
            raise ValueError(f"unsupported mesh event kind: {self.kind}")
        if not isinstance(self.tags, tuple):
            raise TypeError("tags must be a tuple")
        if not isinstance(self.content, Mapping):
            raise TypeError("content must be a mapping")
        reject_forbidden_content(self.content)
        if self.data_classification not in ALLOWED_DATA_CLASSIFICATIONS:
            raise ValueError("Apollo Mesh V0 events must stay founder_private")
        if self.redistribution not in ALLOWED_REDISTRIBUTION:
            raise ValueError("unsupported mesh redistribution policy")
        if self.public_export_allowed:
            raise ValueError("Apollo Mesh V0 events cannot be marked public-exportable")
        if self.prev_hash is not None and not self.prev_hash.startswith("sha256:"):
            raise ValueError("prev_hash must be sha256-prefixed when present")
        if not self.signer_key_id.startswith("mesh-key:"):
            raise ValueError("signer_key_id must be mesh-key-prefixed")
        if not self.signature.startswith(SIGNATURE_PREFIX):
            raise ValueError("signature must be hmac-sha256-prefixed")
        if not isinstance(self.authority, MeshAuthorityLocks):
            raise TypeError("authority must be MeshAuthorityLocks")


def load_or_create_identity(
    path: str | Path,
    *,
    node_id: str,
    secret: str | None = None,
    created_at: datetime | None = None,
) -> ApolloMeshIdentity:
    identity_path = Path(path)
    if identity_path.exists():
        return identity_from_json(json.loads(identity_path.read_text(encoding="utf-8")))
    loaded_secret = secret or os.environ.get(MESH_SECRET_ENV) or secrets.token_hex(32)
    now = (created_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    identity = ApolloMeshIdentity(
        node_id=node_id,
        key_id=key_id_for_secret(loaded_secret),
        secret=loaded_secret,
        created_at=now,
        node_role=FOUNDER_NODE_ROLE,
    )
    identity_path.parent.mkdir(parents=True, exist_ok=True)
    identity_path.write_text(json.dumps(to_jsonable(identity), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return identity


def identity_from_json(payload: Mapping[str, Any]) -> ApolloMeshIdentity:
    return ApolloMeshIdentity(
        node_id=_required_text(payload.get("node_id"), "node_id"),
        key_id=_required_text(payload.get("key_id"), "key_id"),
        secret=_required_text(payload.get("secret"), "secret"),
        created_at=_parse_datetime(payload.get("created_at"), "created_at"),
        node_role=_optional_text(payload.get("node_role")) or FOUNDER_NODE_ROLE,
    )


def create_mesh_event(
    *,
    identity: ApolloMeshIdentity,
    kind: str,
    content: Mapping[str, Any],
    tags: tuple[str, ...] = (),
    prev_hash: str | None = None,
    created_at: datetime | None = None,
) -> ApolloMeshEvent:
    reject_forbidden_content(content)
    observed = (created_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    unsigned = unsigned_payload(
        from_node=identity.node_id,
        node_role=identity.node_role,
        created_at=observed,
        kind=kind,
        tags=tags,
        content=content,
        data_classification=FOUNDER_PRIVATE,
        redistribution=DO_NOT_EXPORT,
        public_export_allowed=False,
        prev_hash=prev_hash,
        signer_key_id=identity.key_id,
    )
    event_id = event_hash(unsigned)
    return ApolloMeshEvent(
        protocol=MESH_PROTOCOL,
        schema_version=MESH_SCHEMA_VERSION,
        event_id=event_id,
        from_node=identity.node_id,
        node_role=identity.node_role,
        created_at=observed,
        kind=kind,
        tags=tuple(_text(tag) for tag in tags if _text(tag)),
        content=dict(content),
        data_classification=FOUNDER_PRIVATE,
        redistribution=DO_NOT_EXPORT,
        public_export_allowed=False,
        prev_hash=prev_hash,
        signer_key_id=identity.key_id,
        signature=sign_event_id(event_id, identity.secret),
        authority=MeshAuthorityLocks(),
    )


def verify_mesh_event(event: ApolloMeshEvent, *, secret: str) -> bool:
    unsigned = unsigned_payload(
        from_node=event.from_node,
        node_role=event.node_role,
        created_at=event.created_at,
        kind=event.kind,
        tags=event.tags,
        content=event.content,
        data_classification=event.data_classification,
        redistribution=event.redistribution,
        public_export_allowed=event.public_export_allowed,
        prev_hash=event.prev_hash,
        signer_key_id=event.signer_key_id,
    )
    expected_id = event_hash(unsigned)
    expected_sig = sign_event_id(expected_id, secret)
    return hmac.compare_digest(event.event_id, expected_id) and hmac.compare_digest(
        event.signature,
        expected_sig,
    )


def event_from_json(payload: Mapping[str, Any]) -> ApolloMeshEvent:
    authority = payload.get("authority") or {}
    return ApolloMeshEvent(
        protocol=_required_text(payload.get("protocol"), "protocol"),
        schema_version=int(payload.get("schema_version") or 0),
        event_id=_required_text(payload.get("event_id"), "event_id"),
        from_node=_required_text(payload.get("from_node"), "from_node"),
        node_role=_optional_text(payload.get("node_role")) or FOUNDER_NODE_ROLE,
        created_at=_parse_datetime(payload.get("created_at"), "created_at"),
        kind=_required_text(payload.get("kind"), "kind"),
        tags=tuple(str(tag) for tag in payload.get("tags") or ()),
        content=dict(payload.get("content") or {}),
        data_classification=_optional_text(payload.get("data_classification")) or FOUNDER_PRIVATE,
        redistribution=_optional_text(payload.get("redistribution")) or DO_NOT_EXPORT,
        public_export_allowed=bool(payload.get("public_export_allowed", False)),
        prev_hash=_optional_text(payload.get("prev_hash")),
        signer_key_id=_required_text(payload.get("signer_key_id"), "signer_key_id"),
        signature=_required_text(payload.get("signature"), "signature"),
        authority=MeshAuthorityLocks(
            can_submit_order=bool(authority.get("can_submit_order", False)),
            can_move_funds=bool(authority.get("can_move_funds", False)),
            live_execution_allowed=bool(authority.get("live_execution_allowed", False)),
            can_set_probability=bool(authority.get("can_set_probability", False)),
            can_remote_command=bool(authority.get("can_remote_command", False)),
        ),
    )


def unsigned_payload(
    *,
    from_node: str,
    node_role: str,
    created_at: datetime,
    kind: str,
    tags: tuple[str, ...],
    content: Mapping[str, Any],
    data_classification: str,
    redistribution: str,
    public_export_allowed: bool,
    prev_hash: str | None,
    signer_key_id: str,
) -> dict[str, Any]:
    return {
        "protocol": MESH_PROTOCOL,
        "schema_version": MESH_SCHEMA_VERSION,
        "from_node": from_node,
        "node_role": node_role,
        "created_at": _iso(created_at),
        "kind": kind,
        "tags": list(tags),
        "content": to_jsonable(content),
        "data_classification": data_classification,
        "redistribution": redistribution,
        "public_export_allowed": public_export_allowed,
        "prev_hash": prev_hash,
        "signer_key_id": signer_key_id,
    }


def event_hash(unsigned: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(unsigned).encode("utf-8")).hexdigest()


def sign_event_id(event_id: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), event_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return SIGNATURE_PREFIX + digest


def key_id_for_secret(secret: str) -> str:
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()[:16]
    return "mesh-key:" + digest


def reject_forbidden_content(value: Any, *, path: str = "content") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).strip().lower()
            if key_text in FORBIDDEN_CONTENT_FIELDS:
                raise ValueError(f"mesh event content cannot include forbidden field: {path}.{key}")
            reject_forbidden_content(item, path=f"{path}.{key}")
    elif isinstance(value, list | tuple):
        for idx, item in enumerate(value):
            reject_forbidden_content(item, path=f"{path}[{idx}]")


def to_jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return _iso(value)
    if is_dataclass(value):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [to_jsonable(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(to_jsonable(value), sort_keys=True, separators=(",", ":"))


def dumps_event(event: ApolloMeshEvent) -> str:
    return json.dumps(to_jsonable(event), indent=2, sort_keys=True) + "\n"


def _parse_datetime(value: Any, label: str) -> datetime:
    text = _required_text(value, label)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _required_text(value: Any, label: str) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _optional_text(value: Any) -> str | None:
    text = _text(value)
    return text or None


def _text(value: Any) -> str:
    return str(value or "").strip()
