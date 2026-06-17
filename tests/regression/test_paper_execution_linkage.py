"""Paper-execution linkage contract: journal -> position -> outcome.

Adapted from v1's paper-journal/paper-outcome linkage tests, narrowed to the store
classes. Extends the decision spine to the simulated track record (all paper-only,
invariant #1). Isolated temp DB per test via ``project_root=tmp_path``.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from foxclaw.store import (
    AcceptedCandidateStore,
    DecisionReceiptStore,
    PaperJournalStore,
    PaperOutcomeStore,
    ParseAttemptStore,
    RawEventStore,
)

PAPER_JOURNAL_COLUMNS = {
    "journal_id", "journal_uid", "receipt_id", "decision_id", "candidate_id",
    "attempt_id", "event_id", "source_id", "source_type", "candidate_type",
    "action_type", "action_params_json", "confidence", "reason", "status",
    "created_at", "policy_version", "policy_result", "authority_level", "evidence_hash",
}


def _db(root: Path) -> Path:
    return root / "data" / "grove_core.db"


def _decision(root: Path, *, decision_type: str = "watch", confidence: float = 0.74) -> dict:
    raw = RawEventStore(project_root=root).store_event(
        source_id="source_alpha", source_type="discord", source_event_id="m1",
        raw_content="paper journal input", is_synthetic=False, capture_method="discord_listener",
    )
    attempt = ParseAttemptStore(project_root=root).record_attempt(
        event_id=raw["event_id"], parser_name="foxclaw_parser", parser_version="paper_exec_v0",
        accepted=True, confidence=confidence,
        structured_payload={"candidate_type": "market_news", "summary": "fixture"},
    )
    candidate = AcceptedCandidateStore(project_root=root).create_from_parse_attempt(attempt_id=attempt["attempt_id"])
    return DecisionReceiptStore(project_root=root).create_from_candidate(
        candidate_id=candidate["candidate_id"], decision_type=decision_type,
        confidence=confidence, reason="Fixture bounded decision.", evidence_links=[candidate["receipt_id"]],
    )


def _journal(root: Path, *, action_type: str = "hold", decision_type: str = "watch") -> dict:
    decision = _decision(root, decision_type=decision_type)
    return PaperJournalStore(project_root=root).create_from_decision(
        decision_id=decision["decision_id"], action_type=action_type,
        action_params={"symbol": "BTCUSD"} if action_type.startswith("paper_trade") else {},
        confidence=decision["confidence"], reason="Paper journal linked action.",
    )


def _paper_trade_journal(root: Path) -> dict:
    decision = _decision(root, decision_type="paper_candidate_intent")
    return PaperJournalStore(project_root=root).create_from_decision(
        decision_id=decision["decision_id"], action_type="paper_trade_long",
        action_params={"symbol": "BTC/USD", "quantity": 0.01},
        confidence=0.7, reason="Paper-only long from paper intent.",
    )


# --- journal ---------------------------------------------------------------

def test_paper_journal_table_columns(tmp_path: Path) -> None:
    PaperJournalStore(project_root=tmp_path).init_db()
    with sqlite3.connect(_db(tmp_path)) as conn:
        cols = {str(r[1]) for r in conn.execute("PRAGMA table_info(paper_journal)").fetchall()}
    assert PAPER_JOURNAL_COLUMNS <= cols


def test_valid_decision_creates_journal_entry(tmp_path: Path) -> None:
    receipt = _journal(tmp_path)
    assert receipt["receipt_type"] == "paper_journal"
    assert receipt["action_type"] == "hold"
    assert receipt["policy_result"] == "allow"
    assert str(receipt["evidence_hash"]).startswith("sha256:")


def test_invalid_decision_id_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        PaperJournalStore(project_root=tmp_path).create_from_decision(
            decision_id=999, action_type="hold", confidence=0.7, reason="invalid"
        )


def test_broken_lineage_rejected(tmp_path: Path) -> None:
    decision = _decision(tmp_path)
    with sqlite3.connect(_db(tmp_path)) as conn:
        conn.execute("UPDATE accepted_candidates SET event_id=999 WHERE candidate_id=?", (decision["candidate_id"],))
        conn.commit()
    with pytest.raises(ValueError, match="candidate event_id"):
        PaperJournalStore(project_root=tmp_path).create_from_decision(
            decision_id=decision["decision_id"], action_type="hold", confidence=0.7, reason="broken"
        )


def test_live_and_funds_actions_blocked(tmp_path: Path) -> None:
    decision = _decision(tmp_path)
    store = PaperJournalStore(project_root=tmp_path)
    for action in ("live_trade", "submit_order", "fund_move", "rotate_secret", "destructive_write", "mutate_grove_directly"):
        with pytest.raises(ValueError, match="policy blocked"):
            store.create_from_decision(decision_id=decision["decision_id"], action_type=action, confidence=0.7, reason="blocked")


def test_paper_trade_requires_paper_intent(tmp_path: Path) -> None:
    watch = _decision(tmp_path, decision_type="watch")
    store = PaperJournalStore(project_root=tmp_path)
    with pytest.raises(ValueError, match="policy blocked"):
        store.create_from_decision(
            decision_id=watch["decision_id"], action_type="paper_trade_long",
            action_params={"symbol": "BTCUSD", "quantity": 0.01}, confidence=0.7, reason="no intent",
        )
    intent = _decision(tmp_path, decision_type="paper_candidate_intent")
    ok = store.create_from_decision(
        decision_id=intent["decision_id"], action_type="paper_trade_long",
        action_params={"symbol": "BTCUSD", "quantity": 0.01}, confidence=0.7, reason="from intent",
    )
    assert ok["policy_result"] == "allow"


def test_action_params_must_be_valid_json(tmp_path: Path) -> None:
    decision = _decision(tmp_path)
    with pytest.raises(ValueError, match="valid JSON"):
        PaperJournalStore(project_root=tmp_path).create_from_decision(
            decision_id=decision["decision_id"], action_type="hold", action_params="{bad json", confidence=0.7, reason="x"
        )


def test_duplicate_journal_idempotent(tmp_path: Path) -> None:
    decision = _decision(tmp_path)
    store = PaperJournalStore(project_root=tmp_path)
    store.create_from_decision(decision_id=decision["decision_id"], action_type="hold", confidence=0.7, reason="first")
    with pytest.raises(ValueError, match="already exists"):
        store.create_from_decision(decision_id=decision["decision_id"], action_type="hold", confidence=0.7, reason="dup")
    existing = store.create_from_decision(decision_id=decision["decision_id"], action_type="hold", confidence=0.7, reason="idem", allow_duplicate=True)
    assert existing["duplicate"] is True


# --- position / outcome ----------------------------------------------------

def test_open_and_close_position_produces_outcome(tmp_path: Path) -> None:
    journal = _paper_trade_journal(tmp_path)
    store = PaperOutcomeStore(project_root=tmp_path)
    pos = store.open_position(journal["journal_id"], "BTC/USD", "long", entry_price=100.0, quantity=2.0)
    assert pos["receipt_type"] == "paper_position"
    assert pos["unrealized_pnl_usd"] == 0.0

    outcome = store.close_position(pos["position_id"], exit_price=110.0, exit_reason="tp")
    assert outcome["receipt_type"] == "paper_outcome"
    assert outcome["realized_pnl_usd"] == pytest.approx(20.0)  # (110-100)*2 long
    assert outcome["exit_reason"] == "tp"
    # closing removes the open position
    assert store.position_for_journal(journal["journal_id"]) is None


def test_outcome_links_full_chain_back_to_raw_event(tmp_path: Path) -> None:
    journal = _paper_trade_journal(tmp_path)
    store = PaperOutcomeStore(project_root=tmp_path)
    pos = store.open_position(journal["journal_id"], "BTC/USD", "long", entry_price=100.0, quantity=1.0)
    store.close_position(pos["position_id"], exit_price=90.0, exit_reason="sl")
    with sqlite3.connect(_db(tmp_path)) as conn:
        count = conn.execute(
            """
            SELECT COUNT(*) FROM paper_outcomes o
            JOIN paper_journal j ON j.journal_id = o.journal_id
            JOIN decision_receipts d ON d.decision_id = j.decision_id
            JOIN accepted_candidates c ON c.candidate_id = j.candidate_id
            JOIN parse_attempts p ON p.attempt_id = j.attempt_id
            JOIN raw_events r ON r.event_id = j.event_id
            """
        ).fetchone()[0]
    assert count == 1


def test_position_requires_paper_trade_journal(tmp_path: Path) -> None:
    journal = _journal(tmp_path, action_type="hold")  # not a paper trade
    with pytest.raises(ValueError, match="does not open a paper position"):
        PaperOutcomeStore(project_root=tmp_path).open_position(
            journal["journal_id"], "BTC/USD", "long", entry_price=100.0, quantity=1.0
        )


def test_short_pnl_sign(tmp_path: Path) -> None:
    decision = _decision(tmp_path, decision_type="paper_candidate_intent")
    journal = PaperJournalStore(project_root=tmp_path).create_from_decision(
        decision_id=decision["decision_id"], action_type="paper_trade_short",
        action_params={"symbol": "ETH/USD", "quantity": 3.0}, confidence=0.7, reason="short fixture",
    )
    store = PaperOutcomeStore(project_root=tmp_path)
    pos = store.open_position(journal["journal_id"], "ETH/USD", "short", entry_price=50.0, quantity=3.0)
    outcome = store.close_position(pos["position_id"], exit_price=40.0, exit_reason="tp")
    assert outcome["realized_pnl_usd"] == pytest.approx(30.0)  # (50-40)*3 short profit


def test_portfolio_summary_aggregates_outcomes(tmp_path: Path) -> None:
    store = PaperOutcomeStore(project_root=tmp_path)
    for exit_price, reason in ((110.0, "tp"), (95.0, "sl")):
        decision = _decision(tmp_path, decision_type="paper_candidate_intent")
        journal = PaperJournalStore(project_root=tmp_path).create_from_decision(
            decision_id=decision["decision_id"], action_type="paper_trade_long",
            action_params={"symbol": "BTC/USD", "quantity": 1.0}, confidence=0.7, reason="agg",
        )
        pos = store.open_position(journal["journal_id"], "BTC/USD", "long", entry_price=100.0, quantity=1.0)
        store.close_position(pos["position_id"], exit_price=exit_price, exit_reason=reason)
    summary = store.get_portfolio_summary()
    assert summary["closed_trade_count"] == 2
    assert summary["wins"] == 1
    assert summary["losses"] == 1
    assert summary["total_realized_pnl_usd"] == pytest.approx(5.0)  # +10 and -5
