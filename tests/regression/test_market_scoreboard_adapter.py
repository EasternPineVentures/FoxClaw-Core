"""Regression: the market scoreboard adapter and the full evidence → edge → gate chain.

Proves the customs border holds end to end: closed paper outcomes in the store become
neutral observations + aggregates in the adapter, the engine estimates the edge, grades a
tier, and applies the gate multiplier — producing one receipt-compatible verdict. Also
pins the corruption filters that encode invariant #8 (a mis-parsed price can't fake a
track record) and the source-exclusion / dedup hygiene.
"""
from __future__ import annotations

import sqlite3

import pytest

from foxclaw.adapters.market import (
    assess_setup,
    build_scoreboard,
    clean_rows,
    observations_by_subject,
)
from foxclaw.store.outcomes import PaperOutcomeStore


# --- fixture: a store with seeded closed outcomes ---------------------------

def _seed_outcome(
    conn: sqlite3.Connection,
    *,
    n0: int,
    source_id: str,
    symbol: str,
    side: str,
    entry: float,
    exit_: float,
    source_type: str = "rss",
    exit_time: str = "2026-06-10T00:00:00+00:00",
) -> None:
    """Insert one linked paper_journal + paper_outcomes pair (FK off — we are testing the
    scoreboard read path, not the receipt-spine lineage validation)."""
    jid = n0
    conn.execute(
        """
        INSERT INTO paper_journal (
            journal_id, journal_uid, receipt_id, decision_id, candidate_id, attempt_id,
            event_id, source_id, source_type, candidate_type, action_type,
            action_params_json, confidence, reason, status, created_at,
            policy_version, policy_result, authority_level, evidence_hash
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            jid, f"juid_{jid}", f"jrcpt_{jid}", jid, jid, jid, jid, source_id, source_type,
            "paper_candidate_intent",
            "paper_trade_long" if side == "long" else "paper_trade_short",
            "{}", 0.6, "seed", "logged", exit_time, "v1", "allow", "A2_guarded_record",
            f"sha256:seed{jid}",
        ),
    )
    conn.execute(
        """
        INSERT INTO paper_outcomes (
            receipt_id, position_id, journal_id, journal_receipt_id, symbol, side,
            entry_price, exit_price, quantity, realized_pnl_usd, pnl_usd, entry_time,
            exit_time, exit_reason, max_favorable_excursion, max_adverse_excursion, evidence_hash
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            f"orcpt_{jid}", jid, jid, f"jrcpt_{jid}", symbol, side, entry, exit_, 1.0,
            (exit_ - entry), (exit_ - entry), exit_time, exit_time, "tp", 0.0, 0.0,
            f"sha256:outc{jid}",
        ),
    )


@pytest.fixture()
def seeded_store(tmp_path):
    store = PaperOutcomeStore(db_path=tmp_path / "grove_core.db")
    store.init_db()
    conn = sqlite3.connect(str(store.db_path))  # FK off by default — bypass lineage checks
    try:
        jid = 1
        # A strong winning setup: 12 long trades, +10% each.
        for _ in range(12):
            _seed_outcome(conn, n0=jid, source_id="good_src", symbol="BTC/USD",
                          side="long", entry=100.0, exit_=110.0)
            jid += 1
        # A catastrophic losing setup: 5 short trades, -10% each (exit above entry on a short).
        for _ in range(5):
            _seed_outcome(conn, n0=jid, source_id="bad_src", symbol="ETH/USD",
                          side="short", entry=100.0, exit_=110.0)
            jid += 1
        conn.commit()
    finally:
        conn.close()
    return store


# --- the full chain ---------------------------------------------------------

def test_scoreboard_grades_both_setups(seeded_store):
    board = build_scoreboard(seeded_store)
    assert set(board["by_key"]) == {"good_src:BTC/USD:long", "bad_src:ETH/USD:short"}
    good = board["by_key"]["good_src:BTC/USD:long"]
    bad = board["by_key"]["bad_src:ETH/USD:short"]
    assert good["trades"] == 12 and good["decision"] == "allow_boosted"
    assert good["success_rate"] == 1.0 and good["trust_tier"] == "developing"
    assert bad["trades"] == 5 and bad["decision"] == "block"  # catastrophic mean reward
    assert bad["mean_reward"] < -0.03


def test_assess_winning_setup_runs_full_chain(seeded_store):
    out = assess_setup(seeded_store, "good_src", "BTC/USD", "long", raw_commitment=1.0)
    # gate applied the boosted tier from the scoreboard grade
    assert out["tier"] == "allow_boosted"
    assert out["multiplier"] == 1.20
    assert out["adjusted_commitment"] == pytest.approx(1.2)
    # the edge path also ran: a 12/12 winner is a confident positive edge
    assert out["edge"].n == pytest.approx(12.0)
    assert out["edge"].prob_edge > 0.9
    assert out["edge"].decision in {"allow", "allow_boosted"}


def test_assess_losing_setup_blocks_to_zero(seeded_store):
    out = assess_setup(seeded_store, "bad_src", "ETH/USD", "short", raw_commitment=1.0)
    assert out["tier"] == "block"
    assert out["adjusted_commitment"] == 0.0


def test_assess_unknown_setup_falls_back_to_observe(seeded_store):
    out = assess_setup(seeded_store, "never", "DOGE/USD", "long", raw_commitment=1.0)
    assert out["tier"] == "observe"
    assert out["adjusted_commitment"] == pytest.approx(0.75)
    assert "no history" in out["gate_reason"]


# --- the border: neutral observations ---------------------------------------

def test_observations_are_neutral_success_and_magnitude(seeded_store):
    rows, _ = clean_rows(seeded_store.get_closed_outcomes_with_source())
    by_subject = observations_by_subject(rows)
    good = by_subject["good_src:BTC/USD:long"]
    assert len(good) == 12
    assert all(o.success and o.magnitude == pytest.approx(0.10) for o in good)
    bad = by_subject["bad_src:ETH/USD:short"]
    assert all((not o.success) and o.magnitude == pytest.approx(0.10) for o in bad)


# --- corruption filters: invariant #8 (pure, no DB) -------------------------

def _row(**kw):
    base = dict(source_id="s", source_type="rss", symbol="BTC/USD", side="long",
               entry_price=100.0, exit_price=110.0, pnl_usd=10.0, exit_reason="tp",
               exit_time="2026-06-10T00:00:00+00:00", duplicate_of_event_id=None)
    base.update(kw)
    return base


def test_clean_drops_duplicate_rows():
    kept, counts = clean_rows([_row(), _row(duplicate_of_event_id=42)])
    assert counts["duplicate"] == 1 and len(kept) == 1


def test_clean_drops_excluded_sources():
    kept, counts = clean_rows([_row(), _row(source_type="market_feed"),
                               _row(source_id="synthetic_paper_outcome_smoke")])
    assert counts["excluded"] == 2 and len(kept) == 1


def test_clean_drops_implausible_return():
    # entry 100 -> exit 300 is a +200% single-trade return: corrupt price, dropped.
    kept, counts = clean_rows([_row(), _row(exit_price=300.0)])
    assert counts["corrupt_return"] == 1 and len(kept) == 1


def test_clean_drops_entry_price_outlier():
    # Four sane ~100 entries establish the symbol median; a 500 entry is a mis-parse.
    rows = [_row(exit_price=101.0) for _ in range(4)] + [_row(entry_price=500.0, exit_price=505.0)]
    kept, counts = clean_rows(rows)
    assert counts["corrupt_entry"] == 1 and len(kept) == 4
