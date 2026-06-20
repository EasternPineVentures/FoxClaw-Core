from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BATCH_TOOL = REPO / "tools" / "microscope_batch.py"
PUBLIC_FIXTURE_DIR = REPO / "tests" / "fixtures" / "public_contract"


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


def _insert_candidate(path: Path, candidate_id: int, payload: dict[str, object] | str) -> None:
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
                f"candidate_uid_private_{candidate_id}",
                f"receipt_private_{candidate_id}",
                candidate_id * 10,
                candidate_id * 100,
                "private_source_alpha",
                "discord",
                "parser_fixture_v1",
                "trade_signal",
                payload_json,
                0.91,
                "accepted_candidate_v0",
                "fixture",
                "accepted",
                "2026-06-19T18:00:00+00:00",
                f"sha256:private{candidate_id}",
            ),
        )


def _fixture_db(tmp_path: Path) -> Path:
    db = tmp_path / "grove_core.db"
    _create_db(db)
    _insert_candidate(
        db,
        1,
        {
            "candidate_type": "trade_signal",
            "symbol": "BTC/USD",
            "side": "long",
            "summary": "Fixture signal.",
        },
    )
    return db


def _public_card(name: str = "watch.json") -> dict[str, object]:
    return json.loads((PUBLIC_FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _run_batch(db: Path, output_root: Path, cursor: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(BATCH_TOOL),
            "--after-id",
            "0",
            "--limit",
            "10",
            "--db",
            str(db),
            "--output-root",
            str(output_root),
            "--cursor",
            str(cursor),
            *extra,
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )


def test_batch_dry_run_creates_no_files_and_does_not_move_cursor(tmp_path: Path) -> None:
    db = _fixture_db(tmp_path)
    output_root = tmp_path / "runtime_exports" / "coinfox" / "staging"
    cursor = tmp_path / "runtime_logs" / "microscope_cursor.json"

    completed = _run_batch(db, output_root, cursor, "--dry-run")

    payload = json.loads(completed.stdout)
    assert payload["dry_run"] is True
    assert payload["write_staging"] is False
    assert payload["counts"]["selected"] == 1
    assert not output_root.exists()
    assert not cursor.exists()


def test_batch_write_staging_is_atomic_and_updates_cursor_after_manifest(tmp_path: Path) -> None:
    db = _fixture_db(tmp_path)
    _insert_candidate(
        db,
        2,
        {"candidate_type": "market_news", "summary": "Watch-only fixture."},
    )
    output_root = tmp_path / "runtime_exports" / "coinfox" / "staging"
    cursor = tmp_path / "runtime_logs" / "microscope_cursor.json"

    completed = _run_batch(db, output_root, cursor, "--write-staging", "--run-id", "run_fixture")

    payload = json.loads(completed.stdout)
    run_dir = output_root / "run_fixture"
    assert payload["dry_run"] is False
    assert payload["write_staging"] is True
    assert payload["cursor_updated"] is True
    assert run_dir.exists()
    assert (run_dir / "cards.jsonl").read_text(encoding="utf-8") == ""
    assert (run_dir / "failures.jsonl").read_text(encoding="utf-8") == ""

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["contract_version"] == "1.0.0"
    assert manifest["counts"]["selected"] == 2
    assert manifest["counts"]["cards"] == 0
    assert manifest["counts"]["failures"] == 0
    assert set(manifest["hashes"]) == {"cards", "failures"}
    assert manifest["status"]["coinfox_api_called"] is False
    assert manifest["status"]["coinfox_db_written"] is False
    assert not list(run_dir.glob("*.tmp*"))

    cursor_payload = json.loads(cursor.read_text(encoding="utf-8"))
    assert cursor_payload["last_candidate_id"] == 2
    assert cursor_payload["run_id"] == "run_fixture"


def test_batch_continues_after_malformed_candidate_and_keeps_failure_retriable(
    tmp_path: Path,
) -> None:
    db = tmp_path / "grove_core.db"
    _create_db(db)
    _insert_candidate(db, 1, '{"candidate_type":')
    _insert_candidate(
        db,
        2,
        {"candidate_type": "market_news", "summary": "Still assess this candidate."},
    )
    output_root = tmp_path / "runtime_exports" / "coinfox" / "staging"
    cursor = tmp_path / "runtime_logs" / "microscope_cursor.json"

    completed = _run_batch(db, output_root, cursor, "--write-staging", "--run-id", "run_fail")

    payload = json.loads(completed.stdout)
    assert payload["counts"]["selected"] == 2
    assert payload["counts"]["assessed"] == 1
    assert payload["counts"]["failures"] == 1
    assert payload["cursor_updated"] is False
    assert not cursor.exists()

    failure_lines = (output_root / "run_fail" / "failures.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(failure_lines) == 1
    failure = json.loads(failure_lines[0])
    assert failure["retriable"] is True
    assert failure["error_code"] == "candidate_payload_decode_error"
    assert "candidate_id" not in json.dumps(failure, sort_keys=True)
    assert "receipt_private" not in json.dumps(failure, sort_keys=True)


def test_staged_ids_are_stable_and_collision_safe() -> None:
    from foxclaw.intelligence.staging import staged_card_id

    base = {"assessment_id": "microscope_a", "assessment_version": "microscope_assessment.v0.1"}
    same = {"assessment_id": "microscope_a", "assessment_version": "microscope_assessment.v0.1"}
    other = {"assessment_id": "microscope_b", "assessment_version": "microscope_assessment.v0.1"}

    assert staged_card_id(base) == staged_card_id(same)
    assert staged_card_id(base) != staged_card_id(other)


def test_public_card_validation_runs_after_publication_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    from foxclaw.intelligence import staging

    assessment = {
        "assessment_id": "microscope_public_fixture",
        "assessment_version": "microscope_assessment.v0.1",
        "contract": {"version": "1.0.0"},
        "publication": {"allowed": True, "publication_class": "DERIVATIVE_PUBLIC_SAFE"},
        "public_card": {"bad": True},
    }

    with pytest.raises(staging.PublicCardStagingError, match="public card failed validation"):
        staging.public_card_for_staging(assessment)


def test_schema_incomplete_approved_card_cannot_reach_staging() -> None:
    from foxclaw.intelligence import staging

    card = _public_card()
    del card["claim"]["why_it_matters_now"]
    assessment = {
        "assessment_id": "microscope_public_fixture",
        "assessment_version": "microscope_assessment.v0.1",
        "contract": {"version": "1.0.0"},
        "publication": {"allowed": True, "publication_class": "DERIVATIVE_PUBLIC_SAFE"},
        "public_card": card,
    }

    with pytest.raises(
        staging.PublicCardStagingError,
        match=r"public card failed validation: \$\.claim\.why_it_matters_now: required",
    ):
        staging.public_card_for_staging(assessment)


def test_staging_suppresses_exact_duplicate_public_ids(tmp_path: Path) -> None:
    from foxclaw.intelligence.staging import write_staging_artifacts

    card = _public_card()
    output_root = tmp_path / "runtime_exports" / "coinfox" / "staging"

    write_staging_artifacts(
        output_root=output_root,
        run_id="duplicates",
        cards=[card, deepcopy(card), deepcopy(card)],
        failures=[],
        counts={"selected": 3, "assessed": 3, "cards": 3, "failures": 0},
        generated_at="2026-06-19T18:00:00+00:00",
    )

    run_dir = output_root / "duplicates"
    card_lines = (run_dir / "cards.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(card_lines) == 1
    assert json.loads(card_lines[0])["public_intelligence_id"] == card["public_intelligence_id"]

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["counts"]["cards"] == 1
    assert manifest["counts"]["duplicates_suppressed"] == 2
    assert manifest["counts"]["duplicate_conflicts"] == 0


def test_staging_conflicting_duplicate_ids_fail_closed_and_stay_sanitized(tmp_path: Path) -> None:
    from foxclaw.intelligence.staging import write_staging_artifacts

    first = _public_card("watch.json")
    conflicting = deepcopy(first)
    conflicting["claim"]["summary"] = "A different public-safe summary."
    unrelated = _public_card("structured.json")
    output_root = tmp_path / "runtime_exports" / "coinfox" / "staging"

    write_staging_artifacts(
        output_root=output_root,
        run_id="conflicts",
        cards=[conflicting, unrelated, first],
        failures=[],
        counts={"selected": 3, "assessed": 3, "cards": 3, "failures": 0},
        generated_at="2026-06-19T18:00:00+00:00",
    )

    run_dir = output_root / "conflicts"
    staged_cards = [
        json.loads(line)
        for line in (run_dir / "cards.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [card["public_intelligence_id"] for card in staged_cards] == [
        unrelated["public_intelligence_id"]
    ]

    failure_lines = (run_dir / "failures.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(failure_lines) == 1
    failure = json.loads(failure_lines[0])
    assert failure["error_code"] == "duplicate_id_conflict"
    assert failure["public_intelligence_id"] == first["public_intelligence_id"]

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["counts"]["cards"] == 1
    assert manifest["counts"]["failures"] == 1
    assert manifest["counts"]["duplicate_conflicts"] == 1
    assert manifest["counts"]["duplicates_suppressed"] == 0

    combined = (run_dir / "manifest.json").read_text(encoding="utf-8") + (
        run_dir / "failures.jsonl"
    ).read_text(encoding="utf-8")
    forbidden = (
        "private_source_alpha",
        "candidate_uid_private",
        "receipt_private",
        "source_id",
        "candidate_id",
        "event_id",
        "attempt_id",
        "evidence_hash",
    )
    for fragment in forbidden:
        assert fragment not in combined


def test_staging_duplicate_ordering_is_deterministic(tmp_path: Path) -> None:
    from foxclaw.intelligence.staging import write_staging_artifacts

    cards = [_public_card("structured.json"), _public_card("watch.json")]
    output_root = tmp_path / "runtime_exports" / "coinfox" / "staging"

    write_staging_artifacts(
        output_root=output_root,
        run_id="ordering",
        cards=[cards[0], cards[1], deepcopy(cards[0])],
        failures=[],
        counts={"selected": 3, "assessed": 3, "cards": 3, "failures": 0},
        generated_at="2026-06-19T18:00:00+00:00",
    )

    staged_ids = [
        json.loads(line)["public_intelligence_id"]
        for line in (output_root / "ordering" / "cards.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert staged_ids == sorted({card["public_intelligence_id"] for card in cards})
