"""Paper journal — the simulated action logged from a decision receipt.

Ported from v1 ``src/grovecore/paper_journal.py``. Carries its own action-level policy
(``evaluate_paper_action_policy``) because it is the journal's single consumer; this keeps
paper-only enforcement (invariant #1) right next to where actions are recorded.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect, normalize_key, record_from_row, resolve_db, slugify, utc_now
from .decisions import DecisionReceiptStore

PAPER_JOURNAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_journal (
    journal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_uid TEXT NOT NULL UNIQUE,
    receipt_id TEXT NOT NULL UNIQUE,

    decision_id INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    attempt_id INTEGER,
    event_id INTEGER NOT NULL,

    source_id TEXT NOT NULL,
    source_type TEXT,
    candidate_type TEXT,

    action_type TEXT NOT NULL,
    action_params_json TEXT NOT NULL DEFAULT '{}',

    confidence REAL NOT NULL,
    reason TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'logged',
    created_at TEXT NOT NULL,

    policy_version TEXT NOT NULL,
    policy_result TEXT NOT NULL,
    authority_level TEXT NOT NULL,

    evidence_hash TEXT NOT NULL,

    FOREIGN KEY (decision_id) REFERENCES decision_receipts(decision_id),
    FOREIGN KEY (candidate_id) REFERENCES accepted_candidates(candidate_id),
    FOREIGN KEY (attempt_id) REFERENCES parse_attempts(attempt_id),
    FOREIGN KEY (event_id) REFERENCES raw_events(event_id)
);
"""

PAPER_JOURNAL_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_paper_journal_decision_unique ON paper_journal(decision_id);",
    "CREATE INDEX IF NOT EXISTS idx_paper_journal_event ON paper_journal(event_id);",
    "CREATE INDEX IF NOT EXISTS idx_paper_journal_candidate ON paper_journal(candidate_id);",
    "CREATE INDEX IF NOT EXISTS idx_paper_journal_source_time ON paper_journal(source_id, created_at);",
    "CREATE INDEX IF NOT EXISTS idx_paper_journal_action_status ON paper_journal(action_type, status);",
)

ALLOWED_ACTION_TYPES = {"hold", "paper_trade_long", "paper_trade_short", "escalate"}
PAPER_TRADE_ACTION_TYPES = {"paper_trade_long", "paper_trade_short"}
PAPER_SAFE_DECISION_TYPES = {"paper_candidate_intent", "paper_candidate_request"}
BLOCKED_ACTION_TYPES = {
    "live_trade",
    "submit_order",
    "buy",
    "sell",
    "close_position",
    "cancel_live_order",
    "fund_move",
    "rotate_secret",
    "destructive_write",
    "mutate_grove_directly",
}


def _action_params_json(value: dict[str, Any] | str | None) -> str:
    if value is None:
        payload: Any = {}
    elif isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"action_params_json must be valid JSON: {exc}") from exc
    else:
        payload = dict(value)
    if not isinstance(payload, dict):
        raise ValueError("action_params_json must be a JSON object")
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def evidence_hash_for(
    *,
    decision_id: int,
    candidate_id: int,
    attempt_id: int | None,
    event_id: int,
    action_type: str,
    action_params_json: str,
    confidence: float,
    policy_version: str,
) -> str:
    payload = "\n".join(
        [
            str(int(decision_id)),
            str(int(candidate_id)),
            "" if attempt_id is None else str(int(attempt_id)),
            str(int(event_id)),
            str(action_type),
            action_params_json,
            f"{float(confidence):.8f}",
            str(policy_version),
        ]
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def evaluate_paper_action_policy(*, action_type: str, decision_type: str) -> dict[str, str]:
    action = normalize_key(action_type)
    decision = normalize_key(decision_type)
    if action in BLOCKED_ACTION_TYPES:
        return {
            "policy_result": "block",
            "authority_level": "A4_prohibited",
            "reason": "Action is prohibited before explicit live/execution authority gates.",
        }
    if action not in ALLOWED_ACTION_TYPES:
        return {
            "policy_result": "block",
            "authority_level": "A4_prohibited",
            "reason": f"Unsupported paper_journal action_type: {action_type}",
        }
    if action in PAPER_TRADE_ACTION_TYPES and decision not in PAPER_SAFE_DECISION_TYPES:
        return {
            "policy_result": "block",
            "authority_level": "A4_prohibited",
            "reason": "Paper trade journal actions require a paper_candidate_intent decision receipt.",
        }
    if action == "escalate":
        return {
            "policy_result": "escalate_hold",
            "authority_level": "A3_escalate_hold",
            "reason": "Paper journal escalation is recorded as hold-for-review.",
        }
    return {
        "policy_result": "allow",
        "authority_level": "A2_guarded_record",
        "reason": "Action is inside FoxClaw paper journal boundaries.",
    }


class PaperJournalStore:
    """Append-only simulated action journal linked to decision receipts."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        project_root: str | Path | None = None,
    ) -> None:
        self.db_path = resolve_db(db_path, project_root=project_root)
        self.decision_store = DecisionReceiptStore(db_path=self.db_path)

    def init_db(self) -> None:
        self.decision_store.init_db()
        with connect(self.db_path) as conn:
            conn.executescript(PAPER_JOURNAL_SCHEMA)
            for sql in PAPER_JOURNAL_INDEXES:
                conn.execute(sql)
            conn.commit()

    def _decision_lineage(self, decision_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT d.decision_id, d.receipt_id AS decision_receipt_id,
                       d.candidate_id, d.attempt_id, d.event_id, d.source_id,
                       d.source_type, d.candidate_type, d.decision_type,
                       d.confidence AS decision_confidence, d.policy_result AS decision_policy_result,
                       d.authority_level AS decision_authority_level,
                       c.status AS candidate_status, c.attempt_id AS candidate_attempt_id,
                       c.event_id AS candidate_event_id,
                       p.event_id AS parse_event_id, p.accepted AS parse_accepted,
                       r.receipt_id AS raw_receipt_id
                FROM decision_receipts d
                LEFT JOIN accepted_candidates c ON c.candidate_id = d.candidate_id
                LEFT JOIN parse_attempts p ON p.attempt_id = d.attempt_id
                LEFT JOIN raw_events r ON r.event_id = d.event_id
                WHERE d.decision_id = ?
                """,
                (int(decision_id),),
            ).fetchone()
        return record_from_row(row)

    def journal_for_decision(self, decision_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT journal_id, journal_uid, receipt_id, decision_id, candidate_id,
                       attempt_id, event_id, source_id, source_type, candidate_type,
                       action_type, action_params_json, confidence, reason, status,
                       created_at, policy_version, policy_result, authority_level,
                       evidence_hash
                FROM paper_journal
                WHERE decision_id = ?
                ORDER BY journal_id ASC
                LIMIT 1
                """,
                (int(decision_id),),
            ).fetchone()
        record = record_from_row(row)
        if record is not None:
            record["action_params"] = json.loads(str(record.get("action_params_json") or "{}"))
        return record

    def get_journal_entry(self, journal_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT journal_id, journal_uid, receipt_id, decision_id, candidate_id,
                       attempt_id, event_id, source_id, source_type, candidate_type,
                       action_type, action_params_json, confidence, reason, status,
                       created_at, policy_version, policy_result, authority_level,
                       evidence_hash
                FROM paper_journal
                WHERE journal_id = ?
                """,
                (int(journal_id),),
            ).fetchone()
        record = record_from_row(row)
        if record is not None:
            record["action_params"] = json.loads(str(record.get("action_params_json") or "{}"))
        return record

    def create_from_decision(
        self,
        *,
        decision_id: int,
        action_type: str,
        confidence: float,
        reason: str,
        action_params: dict[str, Any] | str | None = None,
        policy_version: str = "paper_journal_v0",
        allow_duplicate: bool = False,
        require_strategy_receipt: bool = False,
    ) -> dict[str, Any]:
        lineage = self._decision_lineage(int(decision_id))
        if not lineage:
            raise ValueError(f"decision_id {decision_id} does not exist")
        if str(lineage.get("candidate_status") or "").lower() != "accepted":
            raise ValueError("decision is not linked to an accepted candidate")
        if int(lineage.get("parse_accepted") or 0) != 1:
            raise ValueError("decision is not linked to an accepted parse_attempt")
        if not lineage.get("raw_receipt_id"):
            raise ValueError("decision is not linked to raw_events")
        if int(lineage.get("candidate_attempt_id") or 0) != int(lineage.get("attempt_id") or 0):
            raise ValueError("candidate attempt_id does not match decision attempt_id")
        if int(lineage.get("candidate_event_id") or 0) != int(lineage.get("event_id") or 0):
            raise ValueError("candidate event_id does not match decision event_id")
        if int(lineage.get("parse_event_id") or 0) != int(lineage.get("event_id") or 0):
            raise ValueError("parse_attempt event_id does not match decision event_id")

        existing = self.journal_for_decision(int(decision_id))
        if existing:
            if not allow_duplicate:
                raise ValueError(f"paper journal entry already exists for decision_id {decision_id}")
            return {"receipt_type": "paper_journal", **existing, "duplicate": True, "storage": "sqlite"}

        action = normalize_key(action_type)
        confidence_value = float(confidence)
        if confidence_value < 0.0 or confidence_value > 1.0:
            raise ValueError("confidence must be between 0 and 1")
        clean_reason = str(reason or "").strip()
        if not clean_reason:
            raise ValueError("reason is required")
        policy = str(policy_version or "").strip()
        if not policy:
            raise ValueError("policy_version is required")
        params_json = _action_params_json(action_params)
        params = json.loads(params_json)
        if require_strategy_receipt and action in PAPER_TRADE_ACTION_TYPES:
            strategy_receipt_id = str(params.get("strategy_receipt_id") or "").strip()
            if not strategy_receipt_id:
                raise ValueError("strategy_receipt_id is required for paper trade journal actions")

        policy_eval = evaluate_paper_action_policy(
            action_type=action,
            decision_type=str(lineage.get("decision_type") or ""),
        )
        if policy_eval["policy_result"] == "block":
            raise ValueError(f"policy blocked action_type {action}: {policy_eval['reason']}")

        now = utc_now()
        timestamp = now.strftime("%Y%m%dT%H%M%SZ")
        uid = uuid.uuid4().hex
        journal_uid = f"pj_{timestamp}_{uid}"
        source_slug = slugify(str(lineage.get("source_id") or "source"), fallback="source")
        receipt_id = f"paper_{source_slug}_{timestamp}_{uid[:8]}"
        created_at = now.isoformat()
        attempt_id = int(lineage["attempt_id"]) if lineage.get("attempt_id") is not None else None
        evidence_hash = evidence_hash_for(
            decision_id=int(decision_id),
            candidate_id=int(lineage["candidate_id"]),
            attempt_id=attempt_id,
            event_id=int(lineage["event_id"]),
            action_type=action,
            action_params_json=params_json,
            confidence=confidence_value,
            policy_version=policy,
        )

        with connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO paper_journal (
                    journal_uid, receipt_id, decision_id, candidate_id, attempt_id,
                    event_id, source_id, source_type, candidate_type, action_type,
                    action_params_json, confidence, reason, status, created_at,
                    policy_version, policy_result, authority_level, evidence_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    journal_uid,
                    receipt_id,
                    int(decision_id),
                    int(lineage["candidate_id"]),
                    attempt_id,
                    int(lineage["event_id"]),
                    lineage.get("source_id"),
                    lineage.get("source_type"),
                    lineage.get("candidate_type"),
                    action,
                    params_json,
                    confidence_value,
                    clean_reason,
                    "logged",
                    created_at,
                    policy,
                    policy_eval["policy_result"],
                    policy_eval["authority_level"],
                    evidence_hash,
                ),
            )
            conn.commit()
            journal_id = int(cursor.lastrowid)

        return {
            "receipt_type": "paper_journal",
            "receipt_id": receipt_id,
            "journal_id": journal_id,
            "journal_uid": journal_uid,
            "decision_id": int(decision_id),
            "candidate_id": int(lineage["candidate_id"]),
            "attempt_id": attempt_id,
            "event_id": int(lineage["event_id"]),
            "source_id": lineage.get("source_id"),
            "source_type": lineage.get("source_type"),
            "candidate_type": lineage.get("candidate_type"),
            "action_type": action,
            "action_params": params,
            "confidence": confidence_value,
            "reason": clean_reason,
            "status": "logged",
            "policy_version": policy,
            "policy_result": policy_eval["policy_result"],
            "authority_level": policy_eval["authority_level"],
            "evidence_hash": evidence_hash,
            "created_at": created_at,
            "storage": "sqlite",
        }

    def get_recent_entries(self, *, since_hours: float = 24.0) -> list[dict[str, Any]]:
        self.init_db()
        since = utc_now().timestamp() - float(since_hours) * 3600
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT journal_id, journal_uid, receipt_id, decision_id, candidate_id,
                       attempt_id, event_id, source_id, source_type, candidate_type,
                       action_type, action_params_json, confidence, reason, status,
                       created_at, policy_version, policy_result, authority_level,
                       evidence_hash
                FROM paper_journal
                ORDER BY journal_id DESC
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
                record["action_params"] = json.loads(str(record.get("action_params_json") or "{}"))
                recent.append(record)
        return recent

    def recent_counts(self, *, since_hours: float = 24.0) -> dict[str, Any]:
        rows = self.get_recent_entries(since_hours=since_hours)
        return {
            "total": len(rows),
            "logged": sum(1 for row in rows if row.get("status") == "logged"),
            "db_path": str(self.db_path),
        }

    def audit_summary(self, *, since_hours: float = 24.0) -> dict[str, Any]:
        counts = self.recent_counts(since_hours=since_hours)
        counts["recent_records"] = self.get_recent_entries(since_hours=since_hours)[:20]
        return counts
