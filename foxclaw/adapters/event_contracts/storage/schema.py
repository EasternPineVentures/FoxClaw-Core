"""Forecast Desk SQLite schema and frozen-schema helpers."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

FORECAST_SCHEMA_VERSION = 2


def initialize_schema(conn: sqlite3.Connection) -> None:
    """Create or migrate the Forecast Desk schema idempotently."""

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS forecast_schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS raw_payloads (
            raw_hash TEXT PRIMARY KEY,
            venue TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            request_json TEXT NOT NULL,
            response_json TEXT NOT NULL,
            archived_path TEXT,
            observed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS series_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            venue TEXT NOT NULL,
            series_id TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT,
            frequency TEXT,
            settlement_sources_json TEXT NOT NULL,
            rules_url TEXT,
            observed_at TEXT NOT NULL,
            raw_payload_hash TEXT NOT NULL,
            FOREIGN KEY(raw_payload_hash) REFERENCES raw_payloads(raw_hash)
        );

        CREATE TABLE IF NOT EXISTS event_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            venue TEXT NOT NULL,
            event_id TEXT NOT NULL,
            series_id TEXT,
            title TEXT NOT NULL,
            category TEXT,
            status TEXT NOT NULL,
            strike_date TEXT,
            settlement_sources_json TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            raw_payload_hash TEXT NOT NULL,
            FOREIGN KEY(raw_payload_hash) REFERENCES raw_payloads(raw_hash)
        );

        CREATE TABLE IF NOT EXISTS market_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            venue TEXT NOT NULL,
            market_id TEXT NOT NULL,
            event_id TEXT,
            series_id TEXT,
            title TEXT NOT NULL,
            subtitle TEXT,
            status TEXT NOT NULL,
            yes_bid TEXT,
            yes_ask TEXT,
            no_bid TEXT,
            no_ask TEXT,
            last_price TEXT,
            volume TEXT NOT NULL,
            open_interest TEXT NOT NULL,
            close_time TEXT,
            expiration_time TEXT,
            result TEXT,
            resolution_rule_text TEXT,
            settlement_sources_json TEXT NOT NULL,
            price_level_structure TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            raw_payload_hash TEXT NOT NULL,
            FOREIGN KEY(raw_payload_hash) REFERENCES raw_payloads(raw_hash)
        );

        CREATE TABLE IF NOT EXISTS orderbook_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            venue TEXT NOT NULL,
            market_id TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            yes_bids_json TEXT NOT NULL,
            no_bids_json TEXT NOT NULL,
            best_yes_bid TEXT,
            best_yes_ask TEXT,
            best_no_bid TEXT,
            best_no_ask TEXT,
            yes_spread TEXT,
            no_spread TEXT,
            depth_yes_at_best TEXT NOT NULL,
            depth_no_at_best TEXT NOT NULL,
            is_tradeable INTEGER NOT NULL,
            invalid_reason TEXT,
            raw_payload_hash TEXT NOT NULL,
            FOREIGN KEY(raw_payload_hash) REFERENCES raw_payloads(raw_hash)
        );

        CREATE TABLE IF NOT EXISTS forecast_receipts (
            receipt_id TEXT PRIMARY KEY,
            market_id TEXT NOT NULL,
            side TEXT NOT NULL,
            verdict TEXT NOT NULL,
            independent_probability TEXT NOT NULL,
            market_probability TEXT,
            costs_total TEXT NOT NULL,
            usable_edge TEXT NOT NULL,
            minimum_usable_edge TEXT NOT NULL,
            evidence_quality TEXT NOT NULL,
            dossier_hash TEXT NOT NULL,
            engine_subject TEXT NOT NULL,
            engine_tier TEXT NOT NULL,
            gate_multiplier TEXT NOT NULL,
            raw_commitment TEXT NOT NULL,
            adjusted_commitment TEXT NOT NULL,
            reason TEXT NOT NULL,
            code_version TEXT NOT NULL,
            mode TEXT NOT NULL,
            receipt_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sync_cursors (
            cursor_key TEXT PRIMARY KEY,
            cursor TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_market_snapshots_market_time
            ON market_snapshots(market_id, observed_at);
        CREATE INDEX IF NOT EXISTS idx_orderbook_snapshots_market_time
            ON orderbook_snapshots(market_id, observed_at);
        CREATE INDEX IF NOT EXISTS idx_raw_payloads_endpoint_time
            ON raw_payloads(endpoint, observed_at);
        CREATE INDEX IF NOT EXISTS idx_forecast_receipts_market_time
            ON forecast_receipts(market_id, created_at);
        """
    )
    conn.execute(
        "INSERT OR REPLACE INTO forecast_schema_meta(key, value) VALUES (?, ?)",
        ("schema_version", str(FORECAST_SCHEMA_VERSION)),
    )
    conn.execute(f"PRAGMA user_version = {FORECAST_SCHEMA_VERSION}")
    conn.commit()


def canonical_schema(conn: sqlite3.Connection) -> dict[str, Any]:
    tables: dict[str, Any] = {}
    for (name,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall():
        cols = []
        for cid, cname, ctype, notnull, dflt, pk in conn.execute(
            f'PRAGMA table_info("{name}")'
        ).fetchall():
            cols.append(
                {
                    "name": cname,
                    "type": (ctype or "").upper(),
                    "notnull": bool(notnull),
                    "default": dflt,
                    "pk": int(pk),
                }
            )
        tables[name] = {"columns": cols}

    indexes = []
    for iname, tbl, sql in conn.execute(
        "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall():
        indexes.append({"name": iname, "table": tbl, "sql": _norm(sql)})
    return {"schema_version": FORECAST_SCHEMA_VERSION, "tables": tables, "indexes": indexes}


def schema_fingerprint(schema: dict[str, Any]) -> str:
    blob = json.dumps(schema, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _norm(sql: str | None) -> str | None:
    if sql is None:
        return None
    return " ".join(sql.split())
