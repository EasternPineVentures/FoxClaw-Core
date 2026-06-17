"""Guard the carried-forward DB schema (invariant #8, asset boundary).

The frozen artifact (config/db_schema.frozen.json) is the contract for grove_core.db.
Two levels of protection:

  1. Always: the frozen artifact is well-formed and its stored fingerprint matches a
     recomputation over its own schema body (catches a corrupted/hand-edited artifact).
  2. When a live DB is reachable (via $FOXCLAW_DB or ./data/grove_core.db, vendor-neutral):
     assert the live schema still matches the frozen fingerprint (catches drift).

Re-freeze deliberately with `python tools/freeze_db_schema.py --db <path>` when the schema
is intentionally evolved; that change should show up as a reviewable diff to the artifact.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FROZEN_JSON = REPO / "config" / "db_schema.frozen.json"

# Load the freeze tool as a module without requiring it to be on the path.
_spec = importlib.util.spec_from_file_location(
    "freeze_db_schema", REPO / "tools" / "freeze_db_schema.py"
)
freeze = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(freeze)  # type: ignore[union-attr]


def _frozen() -> dict:
    assert FROZEN_JSON.exists(), (
        f"missing {FROZEN_JSON} — run `python tools/freeze_db_schema.py --db <path>`"
    )
    return json.loads(FROZEN_JSON.read_text(encoding="utf-8"))


def test_frozen_artifact_is_self_consistent():
    """The artifact's stored fingerprint matches its own schema body."""
    art = _frozen()
    assert freeze.fingerprint(art["schema"]) == art["fingerprint"], (
        "frozen artifact fingerprint does not match its schema body — "
        "it was hand-edited or corrupted; re-freeze from the live DB."
    )
    assert art["table_count"] == len(art["schema"]["tables"])
    assert art["index_count"] == len(art["schema"]["indexes"])


def test_live_schema_matches_frozen():
    """If a live DB is reachable, its schema must match the frozen fingerprint."""
    db = freeze.resolve_db(None)  # $FOXCLAW_DB, else ./data/grove_core.db
    if not db.exists():
        pytest.skip(f"no live DB at {db} (set FOXCLAW_DB to enable drift check)")
    live = freeze.fingerprint(freeze.canonical_schema(db))
    frozen_fp = _frozen()["fingerprint"]
    assert live == frozen_fp, (
        f"DB schema drift: live {live[:12]} != frozen {frozen_fp[:12]}. "
        f"If intentional, re-freeze: python tools/freeze_db_schema.py --db {db}"
    )
