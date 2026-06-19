from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from foxclaw.store.candidates import AcceptedCandidateStore
from foxclaw.store.events import RawEventStore
from foxclaw.store.outcomes import PaperOutcomeStore
from foxclaw.store.parse_attempts import ParseAttemptStore

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "microscope.py"


def _create_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE accepted_candidates (
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
                evidence_hash TEXT NOT NULL
            );
            CREATE INDEX idx_accepted_candidates_evidence_hash
                ON accepted_candidates(evidence_hash);

            CREATE TABLE paper_journal (
                journal_id INTEGER PRIMARY KEY,
                source_id TEXT,
                source_type TEXT
            );
            CREATE TABLE paper_outcomes (
                outcome_id INTEGER PRIMARY KEY,
                receipt_id TEXT,
                position_id INTEGER,
                journal_id INTEGER NOT NULL,
                journal_receipt_id TEXT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                quantity REAL NOT NULL,
                realized_pnl_usd REAL NOT NULL,
                pnl_usd REAL NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT NOT NULL,
                exit_reason TEXT NOT NULL,
                max_favorable_excursion REAL,
                max_adverse_excursion REAL,
                evidence_hash TEXT NOT NULL
            );
            """
        )


def _insert_candidate(
    path: Path,
    *,
    candidate_id: int,
    payload: dict[str, object] | str,
    source_id: str = "private_source_alpha",
    status: str = "accepted",
    confidence: float = 0.99,
) -> None:
    payload_json = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO accepted_candidates (
                candidate_id, candidate_uid, receipt_id, event_id, attempt_id,
                source_id, source_type, parser_version, candidate_type,
                normalized_payload_json, confidence, admission_policy_version,
                admission_reason, status, created_at, evidence_hash
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                candidate_id,
                f"cand_fixture_{candidate_id}",
                f"candidate_fixture_{candidate_id}",
                candidate_id * 10,
                candidate_id * 100,
                source_id,
                "discord",
                "parser_fixture_v1",
                "trade_signal",
                payload_json,
                confidence,
                "accepted_candidate_v0",
                "fixture",
                status,
                "2026-06-19T18:00:00+00:00",
                f"sha256:candidate{candidate_id}",
            ),
        )


def _insert_outcome(
    path: Path,
    *,
    n: int,
    source_id: str = "private_source_alpha",
    symbol: str = "BTC/USD",
    side: str = "long",
    entry: float = 100.0,
    exit_: float = 110.0,
) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO paper_journal (journal_id, source_id, source_type) VALUES (?,?,?)",
            (n, source_id, "discord"),
        )
        conn.execute(
            """
            INSERT INTO paper_outcomes (
                outcome_id, receipt_id, position_id, journal_id, journal_receipt_id,
                symbol, side, entry_price, exit_price, quantity, realized_pnl_usd,
                pnl_usd, entry_time, exit_time, exit_reason, max_favorable_excursion,
                max_adverse_excursion, evidence_hash
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                n,
                f"outcome_fixture_{n}",
                n,
                n,
                f"journal_fixture_{n}",
                symbol,
                side,
                entry,
                exit_,
                1.0,
                exit_ - entry,
                exit_ - entry,
                "2026-06-10T00:00:00+00:00",
                "2026-06-10T00:00:00+00:00",
                "tp",
                0.0,
                0.0,
                f"sha256:outcome{n}",
            ),
        )


@pytest.fixture()
def microscope_db(tmp_path: Path) -> Path:
    db = tmp_path / "grove_core.db"
    _create_db(db)
    _insert_candidate(
        db,
        candidate_id=1,
        payload={
            "candidate_type": "trade_signal",
            "symbol": "BTC/USD",
            "side": "long",
            "summary": "Fixture candidate.",
        },
    )
    return db


def _schema_fingerprint(path: Path) -> tuple[int, list[tuple]]:
    before = path.read_bytes()
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
        ).fetchall()
    return (hash(before), rows)


def test_readonly_reader_does_not_create_missing_database(tmp_path: Path) -> None:
    from foxclaw.store.candidate_reader import CandidateDatabaseMissingError, ReadOnlyCandidateReader

    missing = tmp_path / "missing.db"
    with pytest.raises(CandidateDatabaseMissingError):
        ReadOnlyCandidateReader(missing).get_candidate(1)
    assert not missing.exists()


def test_readonly_connection_uses_mode_ro_and_query_only(microscope_db: Path) -> None:
    from foxclaw.store.candidate_reader import connect_readonly, readonly_uri_for

    assert readonly_uri_for(microscope_db).endswith("?mode=ro")
    with connect_readonly(microscope_db) as conn:
        assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("CREATE TABLE should_fail (id INTEGER)")


def test_candidate_query_returns_exact_shape_and_preserves_database(microscope_db: Path) -> None:
    from foxclaw.store.candidate_reader import ACCEPTED_CANDIDATE_COLUMNS, ReadOnlyCandidateReader

    before = _schema_fingerprint(microscope_db)
    candidate = ReadOnlyCandidateReader(microscope_db).get_candidate(1)
    after = _schema_fingerprint(microscope_db)

    assert before == after
    assert candidate is not None
    assert tuple(candidate) == ACCEPTED_CANDIDATE_COLUMNS
    assert candidate["candidate_id"] == 1


def test_reader_supports_ordered_reading_after_candidate_id(microscope_db: Path) -> None:
    from foxclaw.store.candidate_reader import ReadOnlyCandidateReader

    _insert_candidate(
        microscope_db,
        candidate_id=2,
        payload={"candidate_type": "market_news", "summary": "Second"},
    )
    rows = ReadOnlyCandidateReader(microscope_db).iter_after(candidate_id=1, limit=10)
    assert [row["candidate_id"] for row in rows] == [2]


def test_microscope_call_path_does_not_use_writable_store_init_db(
    microscope_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from foxclaw.intelligence.microscope import assess_candidate

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("writable store path was called")

    monkeypatch.setattr(AcceptedCandidateStore, "get_candidate", fail)
    monkeypatch.setattr(AcceptedCandidateStore, "init_db", fail)
    monkeypatch.setattr(RawEventStore, "init_db", fail)
    monkeypatch.setattr(ParseAttemptStore, "init_db", fail)
    monkeypatch.setattr(PaperOutcomeStore, "init_db", fail)

    assessment = assess_candidate(candidate_id=1, db_path=microscope_db)

    assert "candidate" not in assessment
    assert assessment["publication"]["publication_class"] == "INTERNAL_ONLY"


def test_summary_only_candidate_produces_private_assessment(tmp_path: Path) -> None:
    from foxclaw.intelligence.microscope import assess_candidate

    db = tmp_path / "grove_core.db"
    _create_db(db)
    _insert_candidate(
        db,
        candidate_id=1,
        payload={"candidate_type": "market_news", "summary": "Watch-only fixture."},
    )

    assessment = assess_candidate(candidate_id=1, db_path=db)

    assert assessment["assessment_version"].startswith("microscope_assessment.")
    assert assessment["paper_only"] is True
    assert assessment["published"] is False
    assert assessment["live_ready"] is False
    assert assessment["paper_ready"] is False
    assert assessment["edge"]["available"] is False
    assert assessment["edge"]["reason"] == "insufficient_projection"


def test_no_outcome_history_keeps_edge_unavailable(microscope_db: Path) -> None:
    from foxclaw.intelligence.microscope import assess_candidate

    assessment = assess_candidate(candidate_id=1, db_path=microscope_db)

    assert assessment["edge"]["available"] is False
    assert assessment["edge"]["verdict"] is None
    assert assessment["edge"]["observation_count"] == 0
    assert assessment["edge"]["reason"] == "insufficient_history"
    assert assessment["gate"]["tier"] == "observe"


def test_qualifying_outcomes_use_existing_bayesian_edge(microscope_db: Path) -> None:
    from foxclaw.intelligence.microscope import assess_candidate

    for n in range(1, 4):
        _insert_outcome(microscope_db, n=n)

    assessment = assess_candidate(candidate_id=1, db_path=microscope_db)

    assert assessment["edge"]["available"] is True
    assert assessment["edge"]["observation_count"] == 3
    assert assessment["edge"]["verdict"]["n"] == 3
    assert assessment["edge"]["verdict"]["prob_edge"] > 0.5
    assert assessment["gate"]["tier"] in {"observe", "allow", "allow_boosted", "reduce", "block"}


def test_prior_only_state_is_not_reported_as_observed_edge(microscope_db: Path) -> None:
    from foxclaw.intelligence.microscope import assess_candidate

    _insert_outcome(microscope_db, n=1)
    assessment = assess_candidate(candidate_id=1, db_path=microscope_db)

    assert assessment["edge"]["available"] is False
    assert assessment["edge"]["observation_count"] == 1
    assert assessment["edge"]["verdict"] is None
    assert assessment["edge"]["reason"] == "insufficient_history"


def test_assessment_id_is_deterministic_and_not_timestamp_only(microscope_db: Path) -> None:
    from foxclaw.intelligence.microscope import assess_candidate

    first = assess_candidate(
        candidate_id=1,
        db_path=microscope_db,
        generated_at="2026-06-19T18:00:00+00:00",
    )
    second = assess_candidate(
        candidate_id=1,
        db_path=microscope_db,
        generated_at="2026-06-19T18:00:01+00:00",
    )
    _insert_candidate(
        microscope_db,
        candidate_id=2,
        payload={"candidate_type": "market_news", "summary": "Second"},
    )
    other = assess_candidate(
        candidate_id=2,
        db_path=microscope_db,
        generated_at="2026-06-19T18:00:00+00:00",
    )

    assert first["assessment_id"] == second["assessment_id"]
    assert first["generated_at"] != second["generated_at"]
    assert first["assessment_id"] != other["assessment_id"]


def test_confidence_does_not_make_risk_edge_or_paper_ready(microscope_db: Path) -> None:
    from foxclaw.intelligence.microscope import assess_candidate

    assessment = assess_candidate(candidate_id=1, db_path=microscope_db)

    assert "candidate" not in assessment
    assert "0.99" not in json.dumps(assessment, sort_keys=True)
    assert assessment["paper_ready"] is False
    assert assessment["edge"]["available"] is False
    assert assessment["readiness"]["scores"]["risk"] == 0


def test_cli_private_preview_labels_and_hides_private_lineage(microscope_db: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--candidate-id", "1", "--db", str(microscope_db)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "PRIVATE" in completed.stdout
    assert "NOT PUBLISHED" in completed.stdout
    assert "PAPER-ONLY" in completed.stdout
    assert "private_source_alpha" not in completed.stdout
    assert "candidate_fixture_1" not in completed.stdout
    assert "sha256:candidate1" not in completed.stdout


def test_cli_json_outputs_one_compact_private_object(microscope_db: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--candidate-id",
            "1",
            "--db",
            str(microscope_db),
            "--json",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert len([line for line in completed.stdout.splitlines() if line.strip()]) == 1
    payload = json.loads(completed.stdout)
    assert payload["published"] is False
    assert payload["publication"]["publication_class"] == "INTERNAL_ONLY"


def test_cli_exits_nonzero_for_missing_candidate(microscope_db: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--candidate-id", "999", "--db", str(microscope_db), "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
    )

    assert completed.returncode != 0
    assert "not found" in completed.stderr.lower()
