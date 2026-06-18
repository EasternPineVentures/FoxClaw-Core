"""Adapter-local repositories for Forecast Desk snapshots."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from foxclaw.adapters.event_contracts.contracts import ForecastReceipt
from foxclaw.adapters.event_contracts.intake import EvidencePacket, IntakeValidation
from foxclaw.adapters.event_contracts.markets import (
    dumps_json,
    NormalizedEvent,
    NormalizedMarket,
    NormalizedOrderBook,
    NormalizedSeries,
    to_jsonable,
)

from .db import connect, resolve_forecast_db
from .schema import initialize_schema


class ForecastRepository:
    def __init__(self, db_path: str | Path | None = None, *, project_root: str | Path | None = None) -> None:
        self.db_path = resolve_forecast_db(db_path, project_root=project_root)

    def init_db(self) -> None:
        with connect(self.db_path) as conn:
            initialize_schema(conn)

    def record_raw_payload(
        self,
        *,
        raw_hash: str,
        venue: str,
        endpoint: str,
        request: Mapping[str, Any] | None,
        response: Mapping[str, Any],
        observed_at: datetime | None = None,
        archived_path: str | Path | None = None,
    ) -> None:
        observed = _iso(observed_at)
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            conn.execute(
                """
                INSERT OR IGNORE INTO raw_payloads (
                    raw_hash, venue, endpoint, request_json, response_json, archived_path, observed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    raw_hash,
                    venue,
                    endpoint,
                    _json(request or {}),
                    _json(response),
                    str(archived_path) if archived_path else None,
                    observed,
                ),
            )
            conn.commit()

    def record_series(self, series: NormalizedSeries) -> str:
        snapshot_id = _snapshot_id("series", series.series_id, series.raw_payload_hash)
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            conn.execute(
                """
                INSERT OR IGNORE INTO series_snapshots (
                    snapshot_id, venue, series_id, title, category, frequency,
                    settlement_sources_json, rules_url, observed_at, raw_payload_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    series.venue,
                    series.series_id,
                    series.title,
                    series.category,
                    series.frequency,
                    _json(series.settlement_sources),
                    series.rules_url,
                    _iso(series.observed_at),
                    series.raw_payload_hash,
                ),
            )
            conn.commit()
        return snapshot_id

    def record_event(self, event: NormalizedEvent) -> str:
        snapshot_id = _snapshot_id("event", event.event_id, event.raw_payload_hash)
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            conn.execute(
                """
                INSERT OR IGNORE INTO event_snapshots (
                    snapshot_id, venue, event_id, series_id, title, category, status,
                    strike_date, settlement_sources_json, observed_at, raw_payload_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    event.venue,
                    event.event_id,
                    event.series_id,
                    event.title,
                    event.category,
                    event.status,
                    _iso(event.strike_date) if event.strike_date else None,
                    _json(event.settlement_sources),
                    _iso(event.observed_at),
                    event.raw_payload_hash,
                ),
            )
            conn.commit()
        return snapshot_id

    def record_market(self, market: NormalizedMarket) -> str:
        snapshot_id = _snapshot_id("market", market.market_id, market.raw_payload_hash)
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            conn.execute(
                """
                INSERT OR IGNORE INTO market_snapshots (
                    snapshot_id, venue, market_id, event_id, series_id, title, subtitle, status,
                    yes_bid, yes_ask, no_bid, no_ask, last_price, volume, open_interest,
                    close_time, expiration_time, result, resolution_rule_text,
                    settlement_sources_json, price_level_structure, observed_at, raw_payload_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    market.venue,
                    market.market_id,
                    market.event_id,
                    market.series_id,
                    market.title,
                    market.subtitle,
                    market.status,
                    _dec(market.yes_bid),
                    _dec(market.yes_ask),
                    _dec(market.no_bid),
                    _dec(market.no_ask),
                    _dec(market.last_price),
                    _dec(market.volume),
                    _dec(market.open_interest),
                    _iso(market.close_time) if market.close_time else None,
                    _iso(market.expiration_time) if market.expiration_time else None,
                    market.result,
                    market.resolution_rule_text,
                    _json(market.settlement_sources),
                    market.price_level_structure,
                    _iso(market.observed_at),
                    market.raw_payload_hash,
                ),
            )
            conn.commit()
        return snapshot_id

    def record_orderbook(self, book: NormalizedOrderBook) -> str:
        snapshot_id = _snapshot_id("orderbook", book.market_id, book.raw_payload_hash)
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            conn.execute(
                """
                INSERT OR IGNORE INTO orderbook_snapshots (
                    snapshot_id, venue, market_id, observed_at, yes_bids_json, no_bids_json,
                    best_yes_bid, best_yes_ask, best_no_bid, best_no_ask, yes_spread, no_spread,
                    depth_yes_at_best, depth_no_at_best, is_tradeable, invalid_reason,
                    raw_payload_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    book.venue,
                    book.market_id,
                    _iso(book.observed_at),
                    _json(to_jsonable(book.yes_bids)),
                    _json(to_jsonable(book.no_bids)),
                    _dec(book.best_yes_bid),
                    _dec(book.best_yes_ask),
                    _dec(book.best_no_bid),
                    _dec(book.best_no_ask),
                    _dec(book.yes_spread),
                    _dec(book.no_spread),
                    _dec(book.depth_yes_at_best),
                    _dec(book.depth_no_at_best),
                    1 if book.is_tradeable else 0,
                    book.invalid_reason,
                    book.raw_payload_hash,
                ),
            )
            conn.commit()
        return snapshot_id

    def save_cursor(self, cursor_key: str, cursor: str | None) -> None:
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            conn.execute(
                """
                INSERT OR REPLACE INTO sync_cursors(cursor_key, cursor, updated_at)
                VALUES (?, ?, ?)
                """,
                (cursor_key, cursor, _iso(None)),
            )
            conn.commit()

    def load_cursor(self, cursor_key: str) -> str | None:
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            row = conn.execute(
                "SELECT cursor FROM sync_cursors WHERE cursor_key = ?",
                (cursor_key,),
            ).fetchone()
        if row is None:
            return None
        return row["cursor"]

    def counts(self) -> dict[str, int]:
        tables = (
            "raw_payloads",
            "series_snapshots",
            "event_snapshots",
            "market_snapshots",
            "orderbook_snapshots",
            "forecast_receipts",
            "trusted_evidence_packets",
            "trusted_evidence_validations",
            "sync_cursors",
        )
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            return {table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}

    def row_by_id(self, table: str, snapshot_id: str) -> sqlite3.Row | None:
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            return conn.execute(f"SELECT * FROM {table} WHERE snapshot_id = ?", (snapshot_id,)).fetchone()

    def record_forecast_receipt(self, receipt: ForecastReceipt) -> str:
        receipt_id = _snapshot_id("forecast_receipt", receipt.market_id, dumps_json(receipt))
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            conn.execute(
                """
                INSERT OR IGNORE INTO forecast_receipts (
                    receipt_id, market_id, side, verdict, independent_probability,
                    market_probability, costs_total, usable_edge, minimum_usable_edge,
                    evidence_quality, dossier_hash, engine_subject, engine_tier,
                    gate_multiplier, raw_commitment, adjusted_commitment, reason,
                    code_version, mode, receipt_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    receipt.market_id,
                    receipt.side,
                    receipt.verdict,
                    _dec(receipt.independent_probability),
                    _dec(receipt.market_probability),
                    _dec(receipt.costs_total),
                    _dec(receipt.usable_edge),
                    _dec(receipt.minimum_usable_edge),
                    _dec(receipt.evidence_quality),
                    receipt.dossier_hash,
                    receipt.engine_subject,
                    receipt.engine_tier,
                    _dec(receipt.gate_multiplier),
                    _dec(receipt.raw_commitment),
                    _dec(receipt.adjusted_commitment),
                    receipt.reason,
                    receipt.code_version,
                    receipt.mode,
                    dumps_json(receipt),
                    _iso(receipt.created_at),
                ),
            )
            conn.commit()
        return receipt_id

    def record_evidence_packet(self, packet: EvidencePacket) -> str:
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            conn.execute(
                """
                INSERT OR IGNORE INTO trusted_evidence_packets (
                    packet_id, submitter_id, trust_tier, market_id, source_id, title, url,
                    source_type, source_classification, claims_json, independence_group,
                    public_information_only_claimed, authority_level, can_set_probability,
                    can_publish, can_enter_paper, can_submit_order, can_move_funds,
                    live_execution_allowed, status, packet_json, raw_payload_hash, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    packet.packet_id,
                    packet.submitter_id,
                    packet.trust_tier,
                    packet.market_id,
                    packet.source_id,
                    packet.title,
                    packet.url,
                    packet.source_type,
                    packet.source_classification,
                    _json(packet.claims),
                    packet.independence_group,
                    _bool(packet.public_information_only_claimed),
                    packet.authority_level,
                    _bool(packet.can_set_probability),
                    _bool(packet.can_publish),
                    _bool(packet.can_enter_paper),
                    _bool(packet.can_submit_order),
                    _bool(packet.can_move_funds),
                    _bool(packet.live_execution_allowed),
                    packet.status,
                    dumps_json(packet),
                    packet.raw_payload_hash,
                    _iso(packet.submitted_at),
                ),
            )
            conn.commit()
        return packet.packet_id

    def record_intake_validation(self, validation: IntakeValidation) -> str:
        with connect(self.db_path) as conn:
            initialize_schema(conn)
            conn.execute(
                """
                INSERT OR IGNORE INTO trusted_evidence_validations (
                    validation_id, packet_id, market_id, source_id, status, accepted_for_dossier,
                    public_information_only, duplicate_key, reasons_json, can_authorize_execution,
                    can_publish, can_enter_paper, can_submit_order, can_move_funds,
                    live_execution_allowed, validation_json, validated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    validation.validation_id,
                    validation.packet_id,
                    validation.market_id,
                    validation.source_id,
                    validation.status,
                    _bool(validation.accepted_for_dossier),
                    _bool(validation.public_information_only),
                    validation.duplicate_key,
                    _json(validation.reasons),
                    _bool(validation.can_authorize_execution),
                    _bool(validation.can_publish),
                    _bool(validation.can_enter_paper),
                    _bool(validation.can_submit_order),
                    _bool(validation.can_move_funds),
                    _bool(validation.live_execution_allowed),
                    dumps_json(validation),
                    _iso(validation.validated_at),
                ),
            )
            conn.commit()
        return validation.validation_id


def _snapshot_id(kind: str, subject: str, raw_hash: str) -> str:
    payload = f"{kind}\n{subject}\n{raw_hash}".encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _iso(value: datetime | None) -> str:
    dt = (value or datetime.now(UTC)).astimezone(UTC)
    return dt.isoformat().replace("+00:00", "Z")


def _dec(value: Any) -> str | None:
    if value is None:
        return None
    return format(value, "f")


def _bool(value: bool) -> int:
    return 1 if value else 0
