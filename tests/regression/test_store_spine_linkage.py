"""Store decision-spine linkage contract (the invariant-encoding regression net).

Adapted from v1's `test_parser_attempt_linkage_contract.py` /
`test_decision_receipt_linkage_contract.py`, narrowed to the store classes (the
tool-subprocess checks port later with their tools). Encodes the receipt chain:

    raw_events -> parse_attempts -> accepted_candidates -> decision_receipts

and the guards that keep it honest (lineage required, policy veto, bounds, idempotency).
Each test uses an isolated temp DB via ``project_root=tmp_path``.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from foxclaw.store import (
    AcceptedCandidateStore,
    DecisionReceiptStore,
    ParseAttemptStore,
    RawEventStore,
)

DECISION_COLUMNS = {
    "decision_id", "decision_uid", "receipt_id", "candidate_id", "attempt_id",
    "event_id", "source_id", "source_type", "candidate_type", "decision_type",
    "confidence", "reason", "evidence_links_json", "policy_version",
    "policy_result", "authority_level", "created_at", "evidence_hash",
}


def _db(root: Path) -> Path:
    return root / "data" / "grove_core.db"


def _raw(root: Path, *, content: str = "decision input") -> dict:
    return RawEventStore(project_root=root).store_event(
        source_id="source_alpha",
        source_type="discord",
        source_event_id="msg-1",
        raw_content=content,
        is_synthetic=False,
        capture_method="discord_listener",
    )


def _attempt(root: Path, *, accepted: bool = True, confidence: float = 0.76) -> dict:
    raw = _raw(root)
    return ParseAttemptStore(project_root=root).record_attempt(
        event_id=raw["event_id"],
        parser_name="foxclaw_parser",
        parser_version="store_spine_v0",
        accepted=accepted,
        confidence=confidence,
        rejection_reason=None if accepted else "missing_required_structure",
        structured_payload={"candidate_type": "market_news", "summary": "watch-only fixture"},
    )


def _candidate(root: Path) -> dict:
    attempt = _attempt(root)
    return AcceptedCandidateStore(project_root=root).create_from_parse_attempt(
        attempt_id=attempt["attempt_id"]
    )


def _decision(root: Path, *, decision_type: str = "watch", confidence: float = 0.74) -> dict:
    candidate = _candidate(root)
    return DecisionReceiptStore(project_root=root).create_from_candidate(
        candidate_id=candidate["candidate_id"],
        decision_type=decision_type,
        confidence=confidence,
        reason="Accepted candidate; bounded watch decision only.",
        evidence_links=[candidate["receipt_id"]],
    )


# --- schema / construction -------------------------------------------------

def test_decision_table_created_with_required_columns(tmp_path: Path) -> None:
    DecisionReceiptStore(project_root=tmp_path).init_db()
    with sqlite3.connect(_db(tmp_path)) as conn:
        cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(decision_receipts)").fetchall()}
    assert DECISION_COLUMNS <= cols


def test_db_resolves_under_project_root(tmp_path: Path) -> None:
    store = RawEventStore(project_root=tmp_path)
    assert store.db_path == _db(tmp_path)


# --- happy path ------------------------------------------------------------

def test_full_chain_produces_linked_decision_receipt(tmp_path: Path) -> None:
    receipt = _decision(tmp_path)
    assert receipt["receipt_type"] == "decision_receipt"
    assert receipt["decision_type"] == "watch"
    assert receipt["policy_result"] == "allow"
    assert receipt["authority_level"] == "A2_guarded_record"
    assert str(receipt["evidence_hash"]).startswith("sha256:")


def test_decision_links_candidate_parse_attempt_and_raw_event(tmp_path: Path) -> None:
    receipt = _decision(tmp_path)
    with sqlite3.connect(_db(tmp_path)) as conn:
        row = conn.execute(
            """
            SELECT d.decision_id, d.candidate_id, d.attempt_id, d.event_id,
                   c.candidate_id, p.attempt_id, r.event_id
            FROM decision_receipts d
            JOIN accepted_candidates c ON c.candidate_id = d.candidate_id
            JOIN parse_attempts p ON p.attempt_id = d.attempt_id
            JOIN raw_events r ON r.event_id = d.event_id
            WHERE d.decision_id = ?
            """,
            (receipt["decision_id"],),
        ).fetchone()
    assert row == (
        receipt["decision_id"], receipt["candidate_id"], receipt["attempt_id"],
        receipt["event_id"], receipt["candidate_id"], receipt["attempt_id"], receipt["event_id"],
    )


# --- guards ----------------------------------------------------------------

def test_broken_lineage_candidate_is_rejected(tmp_path: Path) -> None:
    store = DecisionReceiptStore(project_root=tmp_path)
    store.init_db()
    with sqlite3.connect(_db(tmp_path)) as conn:
        conn.execute(
            """
            INSERT INTO accepted_candidates (
                candidate_id, candidate_uid, receipt_id, event_id, attempt_id,
                source_id, source_type, parser_version, candidate_type,
                normalized_payload_json, confidence, admission_policy_version,
                admission_reason, status, created_at, evidence_hash
            )
            VALUES (42, 'broken', 'cand_broken', 999, 999, 'source_alpha', 'discord',
                    'store_spine_v0', 'market_news', '{"candidate_type":"market_news"}',
                    0.7, 'accepted_candidate_v0', 'broken fixture', 'accepted',
                    '2026-05-25T12:00:00+00:00', 'sha256:broken')
            """
        )
        conn.commit()
    with pytest.raises(ValueError, match="accepted parse_attempt|raw_events"):
        store.create_from_candidate(candidate_id=42, decision_type="watch", confidence=0.7, reason="fail")


def test_unaccepted_candidate_cannot_decide(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    with sqlite3.connect(_db(tmp_path)) as conn:
        conn.execute("UPDATE accepted_candidates SET status='rejected' WHERE candidate_id=?", (candidate["candidate_id"],))
        conn.commit()
    with pytest.raises(ValueError, match="not accepted"):
        DecisionReceiptStore(project_root=tmp_path).create_from_candidate(
            candidate_id=candidate["candidate_id"], decision_type="watch", confidence=0.7, reason="x"
        )


def test_rejected_parse_attempt_cannot_be_promoted(tmp_path: Path) -> None:
    attempt = _attempt(tmp_path, accepted=False, confidence=0.0)
    with pytest.raises(ValueError, match="not accepted"):
        AcceptedCandidateStore(project_root=tmp_path).create_from_parse_attempt(
            attempt_id=attempt["attempt_id"],
            candidate_type="market_news",
            normalized_payload={"candidate_type": "market_news"},
            allow_low_confidence=True,
        )


def test_duplicate_decision_rejected_and_idempotent(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    store = DecisionReceiptStore(project_root=tmp_path)
    store.create_from_candidate(candidate_id=candidate["candidate_id"], decision_type="watch", confidence=0.7, reason="first")
    with pytest.raises(ValueError, match="already exists"):
        store.create_from_candidate(candidate_id=candidate["candidate_id"], decision_type="hold", confidence=0.7, reason="dup")
    existing = store.create_from_candidate(
        candidate_id=candidate["candidate_id"], decision_type="hold", confidence=0.7, reason="idempotent", allow_duplicate=True
    )
    with sqlite3.connect(_db(tmp_path)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM decision_receipts").fetchone()[0] == 1
    assert existing["duplicate"] is True


def test_execution_and_funds_decision_types_blocked(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    store = DecisionReceiptStore(project_root=tmp_path)
    for decision_type in ("scalp_now", "live_trade", "submit_order", "buy", "sell", "fund_move", "rotate_secret"):
        with pytest.raises(ValueError, match="policy blocked"):
            store.create_from_candidate(candidate_id=candidate["candidate_id"], decision_type=decision_type, confidence=0.7, reason="blocked")
    with sqlite3.connect(_db(tmp_path)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM decision_receipts").fetchone()[0] == 0


def test_confidence_out_of_bounds_rejected(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    with pytest.raises(ValueError, match="between 0 and 1"):
        DecisionReceiptStore(project_root=tmp_path).create_from_candidate(
            candidate_id=candidate["candidate_id"], decision_type="watch", confidence=1.1, reason="bad"
        )


def test_empty_reason_rejected(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    with pytest.raises(ValueError, match="reason is required"):
        DecisionReceiptStore(project_root=tmp_path).create_from_candidate(
            candidate_id=candidate["candidate_id"], decision_type="watch", confidence=0.7, reason="   "
        )


def test_duplicate_raw_event_is_flagged(tmp_path: Path) -> None:
    first = _raw(tmp_path, content="identical body")
    second = RawEventStore(project_root=tmp_path).store_event(
        source_id="source_alpha", source_type="discord", raw_content="identical body",
        is_synthetic=False, capture_method="discord_listener",
    )
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert second["duplicate_of_event_id"] == first["event_id"]
