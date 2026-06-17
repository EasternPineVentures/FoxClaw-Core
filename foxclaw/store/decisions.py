"""Decision receipts — the bounded decision at the end of the receipt chain.

Ported from v1 ``src/grovecore/decision_receipts.py``. Every decision is policy-checked
(invariant #1) and lineage-validated against its candidate -> parse attempt -> raw event
before it is recorded. The policy now lives in :mod:`foxclaw.policy.decision_policy`.
"""
from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..policy.decision_policy import evaluate_decision_policy
from .candidates import AcceptedCandidateStore
from .db import connect, json_dumps_list, record_from_row, resolve_db, slugify, utc_now

DECISION_RECEIPTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS decision_receipts (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_uid TEXT NOT NULL UNIQUE,
    receipt_id TEXT NOT NULL UNIQUE,

    candidate_id INTEGER NOT NULL,
    attempt_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,

    source_id TEXT NOT NULL,
    source_type TEXT,

    candidate_type TEXT NOT NULL,
    decision_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    reason TEXT NOT NULL,

    evidence_links_json TEXT NOT NULL DEFAULT '[]',
    policy_version TEXT NOT NULL,
    policy_result TEXT NOT NULL,
    authority_level TEXT NOT NULL,

    created_at TEXT NOT NULL,
    evidence_hash TEXT NOT NULL,

    FOREIGN KEY (candidate_id) REFERENCES accepted_candidates(candidate_id),
    FOREIGN KEY (attempt_id) REFERENCES parse_attempts(attempt_id),
    FOREIGN KEY (event_id) REFERENCES raw_events(event_id)
);
"""

DECISION_RECEIPTS_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_decision_receipts_candidate_unique ON decision_receipts(candidate_id);",
    "CREATE INDEX IF NOT EXISTS idx_decision_receipts_candidate ON decision_receipts(candidate_id);",
    "CREATE INDEX IF NOT EXISTS idx_decision_receipts_attempt ON decision_receipts(attempt_id);",
    "CREATE INDEX IF NOT EXISTS idx_decision_receipts_event ON decision_receipts(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_decision_receipts_source_time ON decision_receipts(source_id, created_at);",
    "CREATE INDEX IF NOT EXISTS idx_decision_receipts_type_confidence ON decision_receipts(decision_type, confidence);",
    "CREATE INDEX IF NOT EXISTS idx_decision_receipts_policy ON decision_receipts(policy_result, authority_level);",
)


def evidence_hash_for(
    *,
    candidate_id: int,
    attempt_id: int,
    event_id: int,
    decision_type: str,
    evidence_links_json: str,
    policy_version: str,
) -> str:
    payload = "\n".join(
        [
            str(int(candidate_id)),
            str(int(attempt_id)),
            str(int(event_id)),
            str(decision_type),
            evidence_links_json,
            str(policy_version),
        ]
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class DecisionReceiptStore:
    """Append-only bounded decision receipts linked to accepted candidates."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        project_root: str | Path | None = None,
    ) -> None:
        self.db_path = resolve_db(db_path, project_root=project_root)
        self.candidate_store = AcceptedCandidateStore(db_path=self.db_path)

    def init_db(self) -> None:
        self.candidate_store.init_db()
        with connect(self.db_path) as conn:
            conn.executescript(DECISION_RECEIPTS_SCHEMA)
            for sql in DECISION_RECEIPTS_INDEXES:
                conn.execute(sql)
            conn.commit()

    def _candidate_lineage(self, candidate_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT c.candidate_id, c.candidate_uid, c.receipt_id AS candidate_receipt_id,
                       c.event_id, c.attempt_id, c.source_id, c.source_type,
                       c.parser_version, c.candidate_type, c.confidence AS candidate_confidence,
                       c.status AS candidate_status, c.evidence_hash AS candidate_evidence_hash,
                       p.receipt_id AS parse_receipt_id, p.event_id AS parse_event_id,
                       p.accepted AS parse_accepted,
                       r.receipt_id AS raw_receipt_id, r.event_id AS raw_event_id
                FROM accepted_candidates c
                LEFT JOIN parse_attempts p ON p.attempt_id = c.attempt_id
                LEFT JOIN raw_events r ON r.event_id = c.event_id
                WHERE c.candidate_id = ?
                """,
                (int(candidate_id),),
            ).fetchone()
        return record_from_row(row)

    def decision_for_candidate(self, candidate_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT decision_id, decision_uid, receipt_id, candidate_id, attempt_id,
                       event_id, source_id, source_type, candidate_type, decision_type,
                       confidence, reason, evidence_links_json, policy_version,
                       policy_result, authority_level, created_at, evidence_hash
                FROM decision_receipts
                WHERE candidate_id = ?
                ORDER BY decision_id ASC
                LIMIT 1
                """,
                (int(candidate_id),),
            ).fetchone()
        return record_from_row(row)

    def get_decision(self, decision_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT decision_id, decision_uid, receipt_id, candidate_id, attempt_id,
                       event_id, source_id, source_type, candidate_type, decision_type,
                       confidence, reason, evidence_links_json, policy_version,
                       policy_result, authority_level, created_at, evidence_hash
                FROM decision_receipts
                WHERE decision_id = ?
                """,
                (int(decision_id),),
            ).fetchone()
        return record_from_row(row)

    def create_from_candidate(
        self,
        *,
        candidate_id: int,
        decision_type: str,
        confidence: float,
        reason: str,
        evidence_links: list[Any] | None = None,
        policy_version: str = "decision_receipt_v0",
        allow_duplicate: bool = False,
    ) -> dict[str, Any]:
        lineage = self._candidate_lineage(int(candidate_id))
        if not lineage:
            raise ValueError(f"accepted candidate_id {candidate_id} does not exist")
        if str(lineage.get("candidate_status") or "").lower() != "accepted":
            raise ValueError(f"candidate_id {candidate_id} is not accepted")
        if not lineage.get("parse_receipt_id") or int(lineage.get("parse_accepted") or 0) != 1:
            raise ValueError("candidate is not linked to an accepted parse_attempt")
        if not lineage.get("raw_receipt_id"):
            raise ValueError("candidate is not linked to raw_events")
        if int(lineage.get("parse_event_id") or 0) != int(lineage.get("event_id") or 0):
            raise ValueError("candidate parse_attempt event_id does not match candidate event_id")

        existing = self.decision_for_candidate(int(candidate_id))
        if existing:
            if not allow_duplicate:
                raise ValueError(f"decision receipt already exists for candidate_id {candidate_id}")
            return {"receipt_type": "decision_receipt", **existing, "duplicate": True, "storage": "sqlite"}

        decision = str(decision_type or "").strip().lower().replace("-", "_").replace(" ", "_")
        confidence_value = float(confidence)
        if confidence_value < 0.0 or confidence_value > 1.0:
            raise ValueError("confidence must be between 0 and 1")
        clean_reason = str(reason or "").strip()
        if not clean_reason:
            raise ValueError("reason is required")
        policy = str(policy_version or "").strip()
        if not policy:
            raise ValueError("policy_version is required")

        policy_eval = evaluate_decision_policy(
            domain="decision_receipt",
            action="create_decision_receipt",
            decision_type=decision,
            actor="foxclaw",
        )
        if policy_eval["policy_result"] == "block":
            raise ValueError(f"policy blocked decision_type {decision}: {policy_eval['reason']}")

        now = utc_now()
        timestamp = now.strftime("%Y%m%dT%H%M%SZ")
        uid = uuid.uuid4().hex
        decision_uid = f"dec_{timestamp}_{uid}"
        source_slug = slugify(str(lineage.get("source_id") or "source"), fallback="source")
        receipt_id = f"decision_{source_slug}_{timestamp}_{uid[:8]}"
        created_at = now.isoformat()
        evidence_json = json_dumps_list(evidence_links)
        evidence_hash = evidence_hash_for(
            candidate_id=int(candidate_id),
            attempt_id=int(lineage["attempt_id"]),
            event_id=int(lineage["event_id"]),
            decision_type=decision,
            evidence_links_json=evidence_json,
            policy_version=policy,
        )

        with connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO decision_receipts (
                    decision_uid, receipt_id, candidate_id, attempt_id, event_id,
                    source_id, source_type, candidate_type, decision_type, confidence,
                    reason, evidence_links_json, policy_version, policy_result,
                    authority_level, created_at, evidence_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_uid,
                    receipt_id,
                    int(candidate_id),
                    int(lineage["attempt_id"]),
                    int(lineage["event_id"]),
                    lineage.get("source_id"),
                    lineage.get("source_type"),
                    lineage.get("candidate_type"),
                    decision,
                    confidence_value,
                    clean_reason,
                    evidence_json,
                    policy,
                    policy_eval["policy_result"],
                    policy_eval["authority_level"],
                    created_at,
                    evidence_hash,
                ),
            )
            conn.commit()
            decision_id = int(cursor.lastrowid)

        return {
            "receipt_type": "decision_receipt",
            "receipt_id": receipt_id,
            "decision_id": decision_id,
            "decision_uid": decision_uid,
            "candidate_id": int(candidate_id),
            "attempt_id": int(lineage["attempt_id"]),
            "event_id": int(lineage["event_id"]),
            "source_id": lineage.get("source_id"),
            "source_type": lineage.get("source_type"),
            "candidate_type": lineage.get("candidate_type"),
            "decision_type": decision,
            "confidence": confidence_value,
            "reason": clean_reason,
            "policy_version": policy,
            "policy_result": policy_eval["policy_result"],
            "authority_level": policy_eval["authority_level"],
            "evidence_hash": evidence_hash,
            "created_at": created_at,
            "storage": "sqlite",
        }

    def get_recent_decisions(self, *, since_hours: float = 24.0) -> list[dict[str, Any]]:
        self.init_db()
        since = utc_now().timestamp() - float(since_hours) * 3600
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT decision_id, decision_uid, receipt_id, candidate_id, attempt_id,
                       event_id, source_id, source_type, candidate_type, decision_type,
                       confidence, reason, policy_version, policy_result, authority_level,
                       created_at, evidence_hash
                FROM decision_receipts
                ORDER BY decision_id DESC
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
            if created.timestamp() >= since:
                recent.append(record)
        return recent

    def recent_counts(self, *, since_hours: float = 24.0) -> dict[str, Any]:
        rows = self.get_recent_decisions(since_hours=since_hours)
        return {
            "total": len(rows),
            "allowed": sum(1 for row in rows if row.get("policy_result") == "allow"),
            "escalate_hold": sum(1 for row in rows if row.get("policy_result") == "escalate_hold"),
            "db_path": str(self.db_path),
        }

    def audit_summary(self, *, since_hours: float = 24.0) -> dict[str, Any]:
        counts = self.recent_counts(since_hours=since_hours)
        counts["recent_records"] = self.get_recent_decisions(since_hours=since_hours)[:20]
        return counts
