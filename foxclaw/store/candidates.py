"""Accepted candidates — promoted parse attempts admitted into the decision pipeline.

Ported from v1 ``src/grovecore/accepted_candidates.py``.
"""
from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect, json_dumps, json_loads, record_from_row, resolve_db, slugify, utc_now
from .parse_attempts import ParseAttemptStore

ACCEPTED_CANDIDATES_SCHEMA = """
CREATE TABLE IF NOT EXISTS accepted_candidates (
    candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_uid TEXT NOT NULL UNIQUE,
    receipt_id TEXT NOT NULL UNIQUE,

    event_id INTEGER NOT NULL,
    attempt_id INTEGER NOT NULL,

    source_id TEXT NOT NULL,
    source_type TEXT,
    parser_version TEXT NOT NULL,

    candidate_type TEXT NOT NULL,
    normalized_payload_json TEXT NOT NULL,

    confidence REAL NOT NULL,
    admission_policy_version TEXT NOT NULL,
    admission_reason TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'accepted',
    created_at TEXT NOT NULL,

    evidence_hash TEXT NOT NULL,

    FOREIGN KEY (event_id) REFERENCES raw_events(event_id),
    FOREIGN KEY (attempt_id) REFERENCES parse_attempts(attempt_id)
);
"""

ACCEPTED_CANDIDATES_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_accepted_candidates_event_id ON accepted_candidates(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_accepted_candidates_attempt_id ON accepted_candidates(attempt_id);",
    "CREATE INDEX IF NOT EXISTS idx_accepted_candidates_source_created ON accepted_candidates(source_id, created_at);",
    "CREATE INDEX IF NOT EXISTS idx_accepted_candidates_type_confidence ON accepted_candidates(candidate_type, confidence);",
    "CREATE INDEX IF NOT EXISTS idx_accepted_candidates_evidence_hash ON accepted_candidates(evidence_hash);",
)

DEFAULT_MIN_CONFIDENCE = 0.60
DEFAULT_ADMISSION_POLICY_VERSION = "accepted_candidate_v0"


def evidence_hash_for(
    *,
    event_id: int,
    attempt_id: int,
    normalized_payload_json: str,
    confidence: float,
    parser_version: str,
) -> str:
    payload = "\n".join(
        [
            str(int(event_id)),
            str(int(attempt_id)),
            normalized_payload_json,
            f"{float(confidence):.8f}",
            str(parser_version),
        ]
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class AcceptedCandidateStore:
    """Append-only accepted candidate receipts linked to parser attempts and raw_events."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        project_root: str | Path | None = None,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ) -> None:
        self.db_path = resolve_db(db_path, project_root=project_root)
        self.min_confidence = float(min_confidence)
        self.parse_store = ParseAttemptStore(db_path=self.db_path)

    def init_db(self) -> None:
        self.parse_store.init_db()
        with connect(self.db_path) as conn:
            conn.executescript(ACCEPTED_CANDIDATES_SCHEMA)
            for sql in ACCEPTED_CANDIDATES_INDEXES:
                conn.execute(sql)
            conn.commit()

    def _parse_attempt(self, attempt_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT attempt_id, attempt_uid, receipt_id, event_id, parser_name,
                       parser_version, accepted, confidence, rejection_reason,
                       structured_payload_json, metadata_json, is_synthetic
                FROM parse_attempts
                WHERE attempt_id = ?
                """,
                (int(attempt_id),),
            ).fetchone()
        return record_from_row(row)

    def _raw_event(self, event_id: int) -> dict[str, Any] | None:
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

    def get_candidate(self, candidate_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT candidate_id, candidate_uid, receipt_id, event_id, attempt_id,
                       source_id, source_type, parser_version, candidate_type,
                       normalized_payload_json, confidence, admission_policy_version,
                       admission_reason, status, created_at, evidence_hash
                FROM accepted_candidates
                WHERE candidate_id = ?
                """,
                (int(candidate_id),),
            ).fetchone()
        return record_from_row(row)

    def candidate_for_attempt(self, attempt_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT candidate_id, candidate_uid, receipt_id, event_id, attempt_id,
                       source_id, source_type, parser_version, candidate_type,
                       confidence, admission_policy_version, admission_reason,
                       status, created_at, evidence_hash
                FROM accepted_candidates
                WHERE attempt_id = ?
                ORDER BY candidate_id ASC
                LIMIT 1
                """,
                (int(attempt_id),),
            ).fetchone()
        return record_from_row(row)

    def candidate_for_evidence_hash(self, evidence_hash: str) -> dict[str, Any] | None:
        self.init_db()
        evidence_hash = str(evidence_hash or "").strip()
        if not evidence_hash:
            return None
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT candidate_id, candidate_uid, receipt_id, event_id, attempt_id,
                       source_id, source_type, parser_version, candidate_type,
                       confidence, admission_policy_version, admission_reason,
                       status, created_at, evidence_hash
                FROM accepted_candidates
                WHERE evidence_hash = ?
                ORDER BY candidate_id ASC
                LIMIT 1
                """,
                (evidence_hash,),
            ).fetchone()
        return record_from_row(row)

    def create_from_parse_attempt(
        self,
        *,
        attempt_id: int,
        candidate_type: str | None = None,
        normalized_payload: dict[str, Any] | None = None,
        confidence: float | None = None,
        admission_policy_version: str = DEFAULT_ADMISSION_POLICY_VERSION,
        admission_reason: str = "accepted_parse_attempt_promoted",
        allow_duplicate: bool = False,
        allow_low_confidence: bool = False,
    ) -> dict[str, Any]:
        attempt = self._parse_attempt(int(attempt_id))
        if not attempt:
            raise ValueError(f"parse attempt_id {attempt_id} does not exist")
        if int(attempt.get("accepted") or 0) != 1:
            raise ValueError(f"parse attempt_id {attempt_id} is not accepted")

        event_id = int(attempt.get("event_id") or 0)
        if event_id <= 0:
            raise ValueError("parse attempt is missing event_id")
        raw_event = self._raw_event(event_id)
        if not raw_event:
            raise ValueError(f"raw event_id {event_id} does not exist")

        existing = self.candidate_for_attempt(int(attempt_id))
        if existing and not allow_duplicate:
            raise ValueError(f"accepted candidate already exists for attempt_id {attempt_id}")

        payload = dict(normalized_payload or {})
        if not payload:
            payload = json_loads(str(attempt.get("structured_payload_json") or "{}"))
        if not payload:
            raise ValueError("normalized payload JSON is required")

        resolved_type = str(candidate_type or payload.get("candidate_type") or payload.get("type") or "").strip()
        if not resolved_type:
            raise ValueError("candidate_type is required")

        parser_version = str(attempt.get("parser_version") or "").strip()
        if not parser_version:
            raise ValueError("parser_version is required")

        confidence_value = float(attempt.get("confidence") if confidence is None else confidence)
        if confidence_value < self.min_confidence and not allow_low_confidence:
            raise ValueError(
                f"confidence {confidence_value:.4f} is below minimum {self.min_confidence:.4f}"
            )
        if confidence_value < 0.0 or confidence_value > 1.0:
            raise ValueError("confidence must be between 0 and 1")

        policy = str(admission_policy_version or "").strip()
        if not policy:
            raise ValueError("admission_policy_version is required")
        reason = str(admission_reason or "").strip()
        if not reason:
            raise ValueError("admission_reason is required")

        now = utc_now()
        timestamp = now.strftime("%Y%m%dT%H%M%SZ")
        uid = uuid.uuid4().hex
        candidate_uid = f"cand_{timestamp}_{uid}"
        parser_slug = slugify(str(attempt.get("parser_name") or "parser"), fallback="parser")
        receipt_id = f"candidate_{parser_slug}_{timestamp}_{uid[:8]}"
        created_at = now.isoformat()
        normalized_json = json_dumps(payload)
        evidence_hash = evidence_hash_for(
            event_id=event_id,
            attempt_id=int(attempt_id),
            normalized_payload_json=normalized_json,
            confidence=confidence_value,
            parser_version=parser_version,
        )
        existing_hash = self.candidate_for_evidence_hash(evidence_hash)
        if existing_hash:
            if allow_duplicate:
                duplicate = dict(existing_hash)
                duplicate.update(
                    {"receipt_type": "accepted_candidate", "duplicate": True, "storage": "sqlite"}
                )
                return duplicate
            raise ValueError(f"accepted candidate already exists for evidence_hash {evidence_hash}")

        with connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO accepted_candidates (
                    candidate_uid, receipt_id, event_id, attempt_id, source_id,
                    source_type, parser_version, candidate_type, normalized_payload_json,
                    confidence, admission_policy_version, admission_reason, status,
                    created_at, evidence_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_uid,
                    receipt_id,
                    event_id,
                    int(attempt_id),
                    raw_event.get("source_id"),
                    raw_event.get("source_type"),
                    parser_version,
                    resolved_type,
                    normalized_json,
                    confidence_value,
                    policy,
                    reason,
                    "accepted",
                    created_at,
                    evidence_hash,
                ),
            )
            conn.commit()
            candidate_id = int(cursor.lastrowid)

        return {
            "receipt_type": "accepted_candidate",
            "receipt_id": receipt_id,
            "candidate_id": candidate_id,
            "candidate_uid": candidate_uid,
            "event_id": event_id,
            "attempt_id": int(attempt_id),
            "source_id": raw_event.get("source_id"),
            "source_type": raw_event.get("source_type"),
            "candidate_type": resolved_type,
            "parser_version": parser_version,
            "confidence": confidence_value,
            "admission_policy_version": policy,
            "admission_reason": reason,
            "status": "accepted",
            "evidence_hash": evidence_hash,
            "created_at": created_at,
            "storage": "sqlite",
        }

    def recent_counts(self, *, since_hours: float = 24.0) -> dict[str, Any]:
        self.init_db()
        since = utc_now().timestamp() - float(since_hours) * 3600
        rows = self._recent_records_since_epoch(since)
        return {
            "total": len(rows),
            "accepted": sum(1 for row in rows if str(row.get("status") or "") == "accepted"),
            "db_path": str(self.db_path),
        }

    def audit_summary(self, *, since_hours: float = 24.0) -> dict[str, Any]:
        counts = self.recent_counts(since_hours=since_hours)
        since = utc_now().timestamp() - float(since_hours) * 3600
        counts["recent_records"] = self._recent_records_since_epoch(since)[:20]
        return counts

    def _recent_records_since_epoch(self, since_epoch: float) -> list[dict[str, Any]]:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT candidate_id, candidate_uid, receipt_id, event_id, attempt_id,
                       source_id, source_type, parser_version, candidate_type,
                       confidence, admission_policy_version, admission_reason,
                       status, created_at, evidence_hash
                FROM accepted_candidates
                ORDER BY candidate_id DESC
                """
            ).fetchall()
        recent: list[dict[str, Any]] = []
        for row in rows:
            record = record_from_row(row)
            try:
                created = datetime.fromisoformat(str(record.get("created_at", "")).replace("Z", "+00:00"))
            except ValueError:
                continue
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            if created.timestamp() >= since_epoch:
                recent.append(record)
        return recent
