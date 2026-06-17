"""Shared storage foundation for the FoxClaw store layer.

This is the v2 fix for two layout scars carried by the v1 `src/grovecore/*` modules:
  1. **Hardcoded DB path.** Every store defaulted to `PROJECT_ROOT/data/grove_core.db`.
     v2 resolves the DB *vendor-neutrally* (invariant #5) — never a cloud-sync path.
  2. **Duplicated helpers.** `utc_now`, `slugify`, JSON (de)serialization and row mapping
     were copy-pasted into every module. They live here once.

The store classes are per-node (invariant #9): each node owns its own `grove_core.db`;
the file is never shared across nodes via a sync service.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# foxclaw-core repo root (…/foxclaw/store/db.py -> repo root is parents[2]).
REPO_ROOT = Path(__file__).resolve().parents[2]

SQLITE_TIMEOUT_S = 30
SQLITE_BUSY_TIMEOUT_MS = 30000


def resolve_db(db_path: str | Path | None = None, *, project_root: str | Path | None = None) -> Path:
    """Locate `grove_core.db` vendor-neutrally — never defaults to a cloud-sync path.

    Resolution order:
      1. explicit ``db_path``
      2. ``project_root/data/grove_core.db`` (used by tests with a tmp root)
      3. ``$FOXCLAW_DB``
      4. ``<repo>/data/grove_core.db`` (local, repo-relative fallback)
    """
    if db_path is not None:
        return Path(db_path).resolve()
    if project_root is not None:
        return (Path(project_root).resolve() / "data" / "grove_core.db")
    env = os.environ.get("FOXCLAW_DB")
    if env:
        return Path(env).resolve()
    return REPO_ROOT / "data" / "grove_core.db"


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a connection with foreign keys on and a generous busy timeout."""
    conn = sqlite3.connect(str(db_path), timeout=SQLITE_TIMEOUT_S)
    conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def slugify(value: str, *, fallback: str = "source") -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return slug[:80] or fallback


def normalize_key(value: Any) -> str:
    """Canonical key form: lowercased, hyphens/spaces collapsed to underscores."""
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def normalize_content(value: str) -> str:
    return "\n".join(
        str(value or "").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    ).strip()


def content_hash_for(source_id: str, source_type: str, raw_content: str) -> str:
    normalized = normalize_content(raw_content)
    payload = "\n".join([str(source_id), str(source_type), normalized]).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def json_dumps(value: dict[str, Any] | None) -> str:
    return json.dumps(dict(value or {}), sort_keys=True, separators=(",", ":"), default=str)


def json_dumps_list(values: list[Any] | None) -> str:
    return json.dumps(list(values or []), sort_keys=True, separators=(",", ":"), default=str)


def json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def record_from_row(row: sqlite3.Row | dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        return {key: row[key] for key in row.keys()}
    return dict(row)
