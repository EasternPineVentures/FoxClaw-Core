"""Parse attempts — the parser audit receipt linked to each raw event.

Ported from v1 ``src/grovecore/parse_attempts.py``.
"""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

from .db import connect, json_dumps, record_from_row, resolve_db, slugify, utc_now
from .events import RawEventStore

PARSE_ATTEMPTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS parse_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_uid TEXT NOT NULL UNIQUE,
    receipt_id TEXT NOT NULL UNIQUE,

    event_id INTEGER NOT NULL,
    parser_name TEXT NOT NULL DEFAULT 'unknown',
    parser_version TEXT NOT NULL,

    attempted_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,

    accepted INTEGER NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 0.0,
    rejection_reason TEXT,

    structured_payload_json TEXT NOT NULL DEFAULT '{}',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    is_synthetic INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (event_id) REFERENCES raw_events(event_id)
);
"""

PARSE_ATTEMPTS_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_parse_attempts_event_time ON parse_attempts(event_id, attempted_at);",
    "CREATE INDEX IF NOT EXISTS idx_parse_attempts_event_parser_version ON parse_attempts(event_id, parser_name, parser_version);",
    "CREATE INDEX IF NOT EXISTS idx_parse_attempts_accepted_time ON parse_attempts(accepted, attempted_at);",
    "CREATE INDEX IF NOT EXISTS idx_parse_attempts_parser_version ON parse_attempts(parser_name, parser_version);",
)


class ParseAttemptStore:
    """Append-only parser attempt receipts linked to GroveCore raw_events."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        project_root: str | Path | None = None,
    ) -> None:
        self.db_path = resolve_db(db_path, project_root=project_root)
        self.raw_store = RawEventStore(db_path=self.db_path)

    def init_db(self) -> None:
        self.raw_store.init_db()
        with connect(self.db_path) as conn:
            conn.executescript(PARSE_ATTEMPTS_SCHEMA)
            for sql in PARSE_ATTEMPTS_INDEXES:
                conn.execute(sql)
            conn.commit()

    def raw_event(self, event_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT event_id, receipt_id, source_id, source_type, source_event_id,
                       observed_at, ingested_at, is_synthetic
                FROM raw_events
                WHERE event_id = ?
                """,
                (int(event_id),),
            ).fetchone()
        return record_from_row(row)

    def record_attempt(
        self,
        *,
        event_id: int,
        parser_version: str,
        accepted: bool,
        confidence: float,
        rejection_reason: str | None = None,
        parser_name: str = "foxclaw_parser",
        structured_payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw_event = self.raw_event(int(event_id))
        if not raw_event:
            raise ValueError(f"raw event_id {event_id} does not exist")
        version = str(parser_version or "").strip()
        if not version:
            raise ValueError("parser_version is required")
        name = str(parser_name or "unknown").strip() or "unknown"
        reason = str(rejection_reason or "").strip()
        if not accepted and not reason:
            raise ValueError("rejection_reason is required for rejected parse attempts")
        confidence_value = max(0.0, min(1.0, float(confidence)))

        now = utc_now()
        timestamp = now.strftime("%Y%m%dT%H%M%SZ")
        uid = uuid.uuid4().hex
        parser_slug = slugify(name, fallback="parser")
        attempt_uid = f"parse_{timestamp}_{parser_slug}_{uid}"
        receipt_id = f"parse_{parser_slug}_{timestamp}_{uid[:8]}"
        attempted_at = now.isoformat()
        completed_at = attempted_at
        synthetic = int(raw_event.get("is_synthetic") or 0)

        with connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO parse_attempts (
                    attempt_uid, receipt_id, event_id, parser_name, parser_version,
                    attempted_at, completed_at, accepted, confidence, rejection_reason,
                    structured_payload_json, metadata_json, is_synthetic
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_uid,
                    receipt_id,
                    int(event_id),
                    name,
                    version,
                    attempted_at,
                    completed_at,
                    1 if accepted else 0,
                    confidence_value,
                    None if accepted and not reason else reason,
                    json_dumps(structured_payload),
                    json_dumps(metadata),
                    synthetic,
                ),
            )
            conn.commit()
            attempt_id = int(cursor.lastrowid)

        return {
            "receipt_type": "parse_attempt",
            "receipt_id": receipt_id,
            "attempt_id": attempt_id,
            "attempt_uid": attempt_uid,
            "event_id": int(event_id),
            "raw_receipt_id": raw_event.get("receipt_id"),
            "source_id": raw_event.get("source_id"),
            "source_type": raw_event.get("source_type"),
            "source_event_id": raw_event.get("source_event_id"),
            "parser_name": name,
            "parser_version": version,
            "attempted_at": attempted_at,
            "completed_at": completed_at,
            "accepted": bool(accepted),
            "confidence": confidence_value,
            "rejection_reason": None if accepted and not reason else reason,
            "is_synthetic": bool(synthetic),
            "storage": "sqlite",
        }
