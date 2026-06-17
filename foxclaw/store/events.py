"""Raw source events — the append-only intake record (the head of the receipt chain).

Ported from v1 ``src/grovecore/raw_events.py``. Behavior preserved, including the
JSONL fallback that keeps intake from losing events when SQLite is briefly unavailable.
Path resolution and shared helpers now come from :mod:`foxclaw.store.db`.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import (
    connect,
    content_hash_for,
    json_dumps,
    normalize_content,
    record_from_row,
    resolve_db,
    slugify,
    utc_now,
    utc_now_iso,
)

RAW_EVENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingest_id TEXT NOT NULL UNIQUE,
    receipt_id TEXT NOT NULL UNIQUE,

    source_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_event_id TEXT,

    observed_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,

    raw_content TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',

    content_hash TEXT NOT NULL,
    is_synthetic INTEGER NOT NULL DEFAULT 0,
    capture_method TEXT NOT NULL DEFAULT 'unknown',

    duplicate_of_event_id INTEGER,
    FOREIGN KEY (duplicate_of_event_id) REFERENCES raw_events(event_id)
);
"""

RAW_EVENTS_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_raw_events_source_time ON raw_events(source_id, ingested_at);",
    "CREATE INDEX IF NOT EXISTS idx_raw_events_ingested_event ON raw_events(ingested_at, event_id);",
    "CREATE INDEX IF NOT EXISTS idx_raw_events_hash_source ON raw_events(content_hash, source_id);",
    "CREATE INDEX IF NOT EXISTS idx_raw_events_synthetic_time ON raw_events(is_synthetic, ingested_at);",
)


def _load_jsonl_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                records.append(parsed)
    except OSError:
        return []
    return records


class RawEventStore:
    """Append-only GroveCore raw source event store."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        project_root: str | Path | None = None,
        fallback_dir: str | Path | None = None,
        force_fallback: bool = False,
    ) -> None:
        self.db_path = resolve_db(db_path, project_root=project_root)
        self.fallback_dir = (
            Path(fallback_dir).resolve()
            if fallback_dir
            else self.db_path.parent / "raw_intake_fallback"
        )
        self.force_fallback = bool(force_fallback)
        self.using_fallback = False
        self.last_init_error = ""

    def init_db(self) -> None:
        if self.force_fallback:
            self.using_fallback = True
            self.fallback_dir.mkdir(parents=True, exist_ok=True)
            return
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with connect(self.db_path) as conn:
                conn.executescript(RAW_EVENTS_SCHEMA)
                for sql in RAW_EVENTS_INDEXES:
                    conn.execute(sql)
                conn.commit()
            self.using_fallback = False
            self.last_init_error = ""
        except (OSError, sqlite3.Error) as exc:
            self.using_fallback = True
            self.last_init_error = str(exc)
            self.fallback_dir.mkdir(parents=True, exist_ok=True)

    def find_duplicate(self, *, content_hash: str, source_id: str) -> dict[str, Any] | None:
        self.init_db()
        if self.using_fallback:
            for record in self._fallback_records():
                if record.get("content_hash") == content_hash and record.get("source_id") == source_id:
                    return record
            return None
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT event_id, ingest_id, receipt_id, source_id, source_type, source_event_id,
                       observed_at, ingested_at, metadata_json, content_hash, is_synthetic,
                       capture_method, duplicate_of_event_id
                FROM raw_events
                WHERE content_hash = ? AND source_id = ?
                ORDER BY event_id ASC
                LIMIT 1
                """,
                (content_hash, source_id),
            ).fetchone()
        return record_from_row(row)

    def store_event(
        self,
        *,
        source_id: str,
        source_type: str,
        raw_content: str,
        source_event_id: str | None = None,
        observed_at: str | None = None,
        metadata: dict[str, Any] | None = None,
        is_synthetic: bool = False,
        capture_method: str = "unknown",
    ) -> dict[str, Any]:
        if not str(source_id or "").strip():
            raise ValueError("source_id is required")
        if not str(source_type or "").strip():
            raise ValueError("source_type is required")
        if not str(raw_content or "").strip():
            raise ValueError("raw_content is required")

        self.init_db()
        now = utc_now()
        timestamp = now.strftime("%Y%m%dT%H%M%SZ")
        source_slug = slugify(source_id)
        uid = uuid.uuid4().hex
        ingest_id = f"ing_{timestamp}_{source_slug}_{uid}"
        receipt_id = f"raw_{source_slug}_{timestamp}_{uid[:8]}"
        observed = str(observed_at or utc_now_iso())
        ingested = now.isoformat()
        normalized_content = normalize_content(raw_content)
        hashed = content_hash_for(source_id, source_type, normalized_content)
        duplicate = self.find_duplicate(content_hash=hashed, source_id=source_id)
        duplicate_of_event_id = int(duplicate["event_id"]) if duplicate and duplicate.get("event_id") else None

        record = {
            "event_id": None,
            "ingest_id": ingest_id,
            "receipt_id": receipt_id,
            "source_id": source_id,
            "source_type": source_type,
            "source_event_id": source_event_id,
            "observed_at": observed,
            "ingested_at": ingested,
            "raw_content": normalized_content,
            "metadata_json": json_dumps(metadata),
            "content_hash": hashed,
            "is_synthetic": 1 if is_synthetic else 0,
            "capture_method": capture_method or "unknown",
            "duplicate_of_event_id": duplicate_of_event_id,
        }

        if self.using_fallback:
            event_id = self._write_fallback(record)
        else:
            with connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO raw_events (
                        ingest_id, receipt_id, source_id, source_type, source_event_id,
                        observed_at, ingested_at, raw_content, metadata_json, content_hash,
                        is_synthetic, capture_method, duplicate_of_event_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["ingest_id"],
                        record["receipt_id"],
                        record["source_id"],
                        record["source_type"],
                        record["source_event_id"],
                        record["observed_at"],
                        record["ingested_at"],
                        record["raw_content"],
                        record["metadata_json"],
                        record["content_hash"],
                        record["is_synthetic"],
                        record["capture_method"],
                        record["duplicate_of_event_id"],
                    ),
                )
                conn.commit()
                event_id = int(cursor.lastrowid)

        return {
            "receipt_type": "raw_event",
            "receipt_id": receipt_id,
            "event_id": event_id,
            "ingest_id": ingest_id,
            "source_id": source_id,
            "source_type": source_type,
            "source_event_id": source_event_id,
            "observed_at": observed,
            "ingested_at": ingested,
            "content_hash": hashed,
            "is_synthetic": bool(is_synthetic),
            "capture_method": capture_method or "unknown",
            "duplicate": duplicate_of_event_id is not None,
            "duplicate_of_event_id": duplicate_of_event_id,
            "storage": "jsonl_fallback" if self.using_fallback else "sqlite",
        }

    def recent_counts(self, *, since_hours: float = 24.0) -> dict[str, Any]:
        self.init_db()
        since = utc_now().timestamp() - float(since_hours) * 3600
        records = self._recent_records_since_epoch(since)
        return {
            "total": len(records),
            "synthetic": sum(1 for row in records if int(row.get("is_synthetic") or 0) == 1),
            "real": sum(1 for row in records if int(row.get("is_synthetic") or 0) == 0),
            "storage": "jsonl_fallback" if self.using_fallback else "sqlite",
        }

    def audit_summary(self, *, since_hours: float = 24.0) -> dict[str, Any]:
        self.init_db()
        since = utc_now().timestamp() - float(since_hours) * 3600
        records = self._recent_records_since_epoch(since)
        safe_records = [
            {
                "event_id": row.get("event_id"),
                "receipt_id": row.get("receipt_id"),
                "source_id": row.get("source_id"),
                "source_type": row.get("source_type"),
                "source_event_id": row.get("source_event_id"),
                "ingested_at": row.get("ingested_at"),
                "is_synthetic": bool(int(row.get("is_synthetic") or 0)),
                "capture_method": row.get("capture_method"),
                "duplicate_of_event_id": row.get("duplicate_of_event_id"),
            }
            for row in records
        ]
        counts = self.recent_counts(since_hours=since_hours)
        counts["recent_records"] = safe_records
        counts["db_path"] = str(self.db_path)
        counts["fallback_dir"] = str(self.fallback_dir)
        counts["fallback_reason"] = self.last_init_error
        return counts

    def _fallback_path(self, when: datetime | None = None) -> Path:
        day = (when or utc_now()).strftime("%Y-%m-%d")
        return self.fallback_dir / f"{day}.raw_events.jsonl"

    def _fallback_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        if not self.fallback_dir.exists():
            return records
        for path in sorted(self.fallback_dir.glob("*.raw_events.jsonl")):
            records.extend(_load_jsonl_records(path))
        return records

    def _write_fallback(self, record: dict[str, Any]) -> int:
        self.fallback_dir.mkdir(parents=True, exist_ok=True)
        records = self._fallback_records()
        next_id = max((int(row.get("event_id") or 0) for row in records), default=0) + 1
        payload = dict(record)
        payload["event_id"] = next_id
        path = self._fallback_path()
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")
        return next_id

    def _recent_records_since_epoch(self, since_epoch: float) -> list[dict[str, Any]]:
        if self.using_fallback:
            records = self._fallback_records()
        else:
            with connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT event_id, ingest_id, receipt_id, source_id, source_type, source_event_id,
                           observed_at, ingested_at, metadata_json, content_hash, is_synthetic,
                           capture_method, duplicate_of_event_id
                    FROM raw_events
                    ORDER BY event_id ASC
                    """
                ).fetchall()
            records = [record_from_row(row) for row in rows]

        recent: list[dict[str, Any]] = []
        for record in records:
            try:
                ingested = datetime.fromisoformat(str(record.get("ingested_at", "")).replace("Z", "+00:00"))
            except ValueError:
                continue
            if ingested.tzinfo is None:
                ingested = ingested.replace(tzinfo=UTC)
            if ingested.timestamp() >= since_epoch:
                recent.append(record)
        return recent
