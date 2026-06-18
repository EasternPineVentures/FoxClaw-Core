from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from foxclaw.adapters.event_contracts.kalshi.models import payload_hash
from foxclaw.adapters.event_contracts.kalshi.normalize import normalize_market
from foxclaw.adapters.event_contracts.storage.db import resolve_forecast_db
from foxclaw.adapters.event_contracts.storage.raw_archive import (
    append_raw_response,
    iter_raw_records,
)
from foxclaw.adapters.event_contracts.storage.repositories import ForecastRepository
from foxclaw.adapters.event_contracts.storage.schema import initialize_schema

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "fixtures" / "kalshi"
SYNC_TOOL = REPO / "tools" / "forecast_desk_sync.py"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_forecast_db_resolver_rejects_cloud_sync_source_of_truth():
    with pytest.raises(ValueError):
        resolve_forecast_db(r"C:\Users\brend\OneDrive\forecast_desk.db")


def test_forecast_schema_initializes_idempotently(tmp_path):
    db = tmp_path / "forecast_desk.db"
    conn = sqlite3.connect(str(db))
    try:
        initialize_schema(conn)
        initialize_schema(conn)
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }
    finally:
        conn.close()
    assert version == 1
    assert {"raw_payloads", "market_snapshots", "orderbook_snapshots", "sync_cursors"} <= tables


def test_raw_archive_round_trips_gzip_jsonl(tmp_path):
    payload = {"ticker": "KXTEST", "yes_bid_dollars": "0.4200"}
    receipt = append_raw_response(
        raw_dir=tmp_path / "raw",
        endpoint="/markets",
        payload=payload,
        request={"limit": 1},
    )
    records = list(iter_raw_records(receipt.archive_path))
    assert len(records) == 1
    assert records[0]["raw_hash"] == payload_hash(payload)
    assert records[0]["payload"] == payload


def test_normalized_market_snapshot_references_raw_payload_hash(tmp_path):
    repo = ForecastRepository(tmp_path / "forecast_desk.db")
    repo.init_db()
    raw = _load("market_detail.json")["market"]
    raw_hash = payload_hash(raw)
    repo.record_raw_payload(
        raw_hash=raw_hash,
        venue="kalshi",
        endpoint="/markets/{ticker}",
        request={"ticker": raw["ticker"]},
        response=raw,
    )
    market = normalize_market(raw)
    snapshot_id = repo.record_market(market)

    with sqlite3.connect(str(repo.db_path)) as conn:
        row = conn.execute(
            """
            SELECT m.market_id, r.raw_hash
            FROM market_snapshots m
            JOIN raw_payloads r ON r.raw_hash = m.raw_payload_hash
            WHERE m.snapshot_id = ?
            """,
            (snapshot_id,),
        ).fetchone()
    assert row == ("KXJOBLESS-26JUN18-T250", raw_hash)


def test_sync_fixture_resume_has_no_duplicate_snapshot_rows(tmp_path):
    db = tmp_path / "forecast_desk.db"
    raw_dir = tmp_path / "raw"

    def run_sync():
        completed = subprocess.run(
            [
                sys.executable,
                str(SYNC_TOOL),
                "--fixture-dir",
                str(FIXTURES),
                "--db",
                str(db),
                "--raw-dir",
                str(raw_dir),
                "--once",
                "--json",
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(completed.stdout)

    first = run_sync()
    second = run_sync()
    assert first["counts"] == second["counts"]
    assert second["counts"]["series_snapshots"] == 1
    assert second["counts"]["event_snapshots"] == 1
    assert second["counts"]["market_snapshots"] == 1
    assert second["counts"]["orderbook_snapshots"] == 1
    assert second["credentials_loaded"] is False
    assert second["order_endpoint_invoked"] is False
