"""Paper positions and realized outcomes — the tail of the receipt chain.

Ported from v1 ``src/grovecore/paper_outcomes.py``. Manages three tables
(``paper_positions``, ``paper_outcomes``, ``position_adjustments``) linked to
``paper_journal``. This is the simulated track record; everything here is paper-only
(invariant #1) — there is no live execution path.

NOTE (architecture review, Phase 1): this module carries market vocabulary
(``realized_pnl_usd``, ``win_rate``, ``sharpe``, ``symbol``, long/short). It lives in
``store/`` per the documented port map, but whether the portfolio *metrics*
(``get_portfolio_summary``) ultimately belong in an analytics adapter is an open
invariant-#4 question, deliberately left for the architecture review rather than decided here.
"""
from __future__ import annotations

import hashlib
import math
import sqlite3
import statistics
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import connect, normalize_key, record_from_row, resolve_db, slugify, utc_now
from .journal import PAPER_TRADE_ACTION_TYPES, PaperJournalStore

PAPER_POSITIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_positions (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_id INTEGER NOT NULL UNIQUE,
    journal_receipt_id TEXT,

    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price REAL NOT NULL,
    quantity REAL NOT NULL,

    open_time TEXT NOT NULL,
    current_price REAL NOT NULL,
    unrealized_pnl_usd REAL NOT NULL DEFAULT 0.0,
    max_favorable_excursion REAL NOT NULL DEFAULT 0.0,
    max_adverse_excursion REAL NOT NULL DEFAULT 0.0,
    last_updated TEXT NOT NULL,

    stop_loss REAL,
    take_profit REAL,

    evidence_hash TEXT NOT NULL,

    FOREIGN KEY (journal_id) REFERENCES paper_journal(journal_id)
);
"""

PAPER_OUTCOMES_SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_outcomes (
    outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id TEXT NOT NULL UNIQUE,
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

    max_favorable_excursion REAL NOT NULL DEFAULT 0.0,
    max_adverse_excursion REAL NOT NULL DEFAULT 0.0,
    evidence_hash TEXT NOT NULL,

    FOREIGN KEY (journal_id) REFERENCES paper_journal(journal_id)
);
"""

POSITION_ADJUSTMENTS_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS position_adjustments ("
    " adjustment_id INTEGER PRIMARY KEY AUTOINCREMENT,"
    " position_id INTEGER NOT NULL, journal_id INTEGER, field TEXT NOT NULL,"
    " old_value REAL, new_value REAL, reason TEXT, source_id TEXT,"
    " adjusted_at TEXT NOT NULL );"
    "CREATE INDEX IF NOT EXISTS idx_position_adjustments_position"
    " ON position_adjustments(position_id);"
)

PAPER_OUTCOME_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_paper_positions_journal ON paper_positions(journal_id);",
    "CREATE INDEX IF NOT EXISTS idx_paper_positions_symbol_time ON paper_positions(symbol, open_time);",
    "CREATE INDEX IF NOT EXISTS idx_paper_outcomes_journal ON paper_outcomes(journal_id);",
    "CREATE INDEX IF NOT EXISTS idx_paper_outcomes_symbol_exit_time ON paper_outcomes(symbol, exit_time);",
    "CREATE INDEX IF NOT EXISTS idx_paper_outcomes_exit_reason ON paper_outcomes(exit_reason);",
)

VALID_SIDES = {"long", "short"}
VALID_EXIT_REASONS = {"tp", "sl", "manual"}
LONG_ACTION = "paper_trade_long"
SHORT_ACTION = "paper_trade_short"


def _clean_symbol(symbol: str) -> str:
    text = str(symbol or "").strip().upper().replace("-", "/")
    if not text:
        raise ValueError("symbol is required")
    if "/" not in text and text.endswith("USD") and len(text) > 3:
        text = f"{text[:-3]}/USD"
    return text


def _clean_side(side: str) -> str:
    value = normalize_key(side)
    if value in {"buy", "paper_trade_long"}:
        value = "long"
    elif value in {"sell", "paper_trade_short"}:
        value = "short"
    if value not in VALID_SIDES:
        raise ValueError("side must be long or short")
    return value


def _positive_float(value: Any, *, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be greater than 0")
    return number


def pnl_for(*, side: str, entry_price: float, current_price: float, quantity: float) -> float:
    clean_side = _clean_side(side)
    if clean_side == "long":
        return (float(current_price) - float(entry_price)) * float(quantity)
    return (float(entry_price) - float(current_price)) * float(quantity)


def _hash_payload(parts: list[Any]) -> str:
    payload = "\n".join(str(part) for part in parts).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def position_evidence_hash_for(
    *, journal_id: int, symbol: str, side: str, entry_price: float, quantity: float, open_time: str
) -> str:
    return _hash_payload(
        ["paper_position_v1", int(journal_id), symbol, side,
         f"{float(entry_price):.12f}", f"{float(quantity):.12f}", open_time]
    )


def outcome_evidence_hash_for(
    *,
    journal_id: int,
    position_id: int | None,
    symbol: str,
    side: str,
    entry_price: float,
    exit_price: float,
    quantity: float,
    realized_pnl_usd: float,
    entry_time: str,
    exit_time: str,
    exit_reason: str,
) -> str:
    return _hash_payload(
        ["paper_outcome_v1", int(journal_id), "" if position_id is None else int(position_id),
         symbol, side, f"{float(entry_price):.12f}", f"{float(exit_price):.12f}",
         f"{float(quantity):.12f}", f"{float(realized_pnl_usd):.12f}",
         entry_time, exit_time, exit_reason]
    )


class PaperOutcomeStore:
    """Simulated paper positions and realized outcomes linked to paper_journal rows."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        project_root: str | Path | None = None,
    ) -> None:
        self.db_path = resolve_db(db_path, project_root=project_root)
        self.journal_store = PaperJournalStore(db_path=self.db_path)

    def init_db(self) -> None:
        self.journal_store.init_db()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with connect(self.db_path) as conn:
            conn.executescript(PAPER_POSITIONS_SCHEMA)
            for _col in ("stop_loss", "take_profit"):
                try:
                    conn.execute(f"ALTER TABLE paper_positions ADD COLUMN {_col} REAL")
                except sqlite3.OperationalError:
                    pass  # column already present
            conn.executescript(PAPER_OUTCOMES_SCHEMA)
            conn.executescript(POSITION_ADJUSTMENTS_SCHEMA)
            for sql in PAPER_OUTCOME_INDEXES:
                conn.execute(sql)
            conn.commit()

    def _journal_lineage(self, journal_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT j.journal_id, j.receipt_id AS journal_receipt_id,
                       j.decision_id, j.candidate_id, j.attempt_id, j.event_id,
                       j.source_id, j.source_type, j.candidate_type, j.action_type,
                       j.action_params_json, j.status AS journal_status,
                       d.decision_id AS linked_decision_id,
                       c.candidate_id AS linked_candidate_id,
                       p.attempt_id AS linked_attempt_id,
                       r.event_id AS linked_event_id,
                       CASE WHEN d.candidate_id = j.candidate_id
                                 AND d.attempt_id = j.attempt_id
                                 AND d.event_id = j.event_id THEN 1 ELSE 0 END AS decision_links_journal,
                       CASE WHEN c.attempt_id = j.attempt_id
                                 AND c.event_id = j.event_id THEN 1 ELSE 0 END AS candidate_links_attempt_raw,
                       CASE WHEN p.event_id = j.event_id THEN 1 ELSE 0 END AS parse_links_raw
                FROM paper_journal j
                LEFT JOIN decision_receipts d ON d.decision_id = j.decision_id
                LEFT JOIN accepted_candidates c ON c.candidate_id = j.candidate_id
                LEFT JOIN parse_attempts p ON p.attempt_id = j.attempt_id
                LEFT JOIN raw_events r ON r.event_id = j.event_id
                WHERE j.journal_id = ?
                """,
                (int(journal_id),),
            ).fetchone()
        return record_from_row(row)

    def _validate_journal_for_position(self, journal_id: int, side: str) -> dict[str, Any]:
        lineage = self._journal_lineage(int(journal_id))
        if not lineage:
            raise ValueError(f"journal_id {journal_id} does not exist")
        action_type = normalize_key(lineage.get("action_type"))
        if action_type not in PAPER_TRADE_ACTION_TYPES:
            raise ValueError("journal action_type does not open a paper position")
        expected_side = "long" if action_type == LONG_ACTION else "short"
        clean_side = _clean_side(side)
        if clean_side != expected_side:
            raise ValueError(f"journal action_type {action_type} requires side {expected_side}")
        if not all(
            [
                lineage.get("linked_decision_id"),
                lineage.get("linked_candidate_id"),
                lineage.get("linked_attempt_id"),
                lineage.get("linked_event_id"),
                int(lineage.get("decision_links_journal") or 0) == 1,
                int(lineage.get("candidate_links_attempt_raw") or 0) == 1,
                int(lineage.get("parse_links_raw") or 0) == 1,
            ]
        ):
            raise ValueError("paper journal lineage is broken")
        return lineage

    def get_position(self, position_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT position_id, journal_id, journal_receipt_id, symbol, side,
                       entry_price, quantity, open_time, current_price,
                       unrealized_pnl_usd, max_favorable_excursion,
                       max_adverse_excursion, last_updated, stop_loss, take_profit,
                       evidence_hash
                FROM paper_positions
                WHERE position_id = ?
                """,
                (int(position_id),),
            ).fetchone()
        return record_from_row(row)

    def position_for_journal(self, journal_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT position_id, journal_id, journal_receipt_id, symbol, side,
                       entry_price, quantity, open_time, current_price,
                       unrealized_pnl_usd, max_favorable_excursion,
                       max_adverse_excursion, last_updated, evidence_hash
                FROM paper_positions
                WHERE journal_id = ?
                """,
                (int(journal_id),),
            ).fetchone()
        return record_from_row(row)

    def outcome_for_journal(self, journal_id: int) -> dict[str, Any] | None:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT outcome_id, receipt_id, position_id, journal_id,
                       journal_receipt_id, symbol, side, entry_price, exit_price,
                       quantity, realized_pnl_usd, pnl_usd, entry_time, exit_time,
                       exit_reason, max_favorable_excursion, max_adverse_excursion,
                       evidence_hash
                FROM paper_outcomes
                WHERE journal_id = ?
                ORDER BY outcome_id ASC
                LIMIT 1
                """,
                (int(journal_id),),
            ).fetchone()
        return record_from_row(row)

    def open_position(
        self,
        journal_id: int,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        *,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> dict[str, Any]:
        lineage = self._validate_journal_for_position(int(journal_id), side)
        existing = self.position_for_journal(int(journal_id))
        if existing:
            return {"receipt_type": "paper_position", "idempotent": True, **existing}
        closed = self.outcome_for_journal(int(journal_id))
        if closed:
            raise ValueError(f"paper outcome already exists for journal_id {journal_id}")

        clean_symbol = _clean_symbol(symbol)
        clean_side = _clean_side(side)
        entry = _positive_float(entry_price, label="entry_price")
        qty = _positive_float(quantity, label="quantity")
        sl_value = float(stop_loss) if stop_loss not in (None, "") else None
        tp_value = float(take_profit) if take_profit not in (None, "") else None
        now = utc_now().isoformat()
        pnl = pnl_for(side=clean_side, entry_price=entry, current_price=entry, quantity=qty)
        evidence_hash = position_evidence_hash_for(
            journal_id=int(journal_id), symbol=clean_symbol, side=clean_side,
            entry_price=entry, quantity=qty, open_time=now,
        )
        with connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO paper_positions (
                    journal_id, journal_receipt_id, symbol, side, entry_price,
                    quantity, open_time, current_price, unrealized_pnl_usd,
                    max_favorable_excursion, max_adverse_excursion, last_updated,
                    stop_loss, take_profit, evidence_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(journal_id), lineage.get("journal_receipt_id"), clean_symbol, clean_side,
                    entry, qty, now, entry, pnl, 0.0, 0.0, now, sl_value, tp_value, evidence_hash,
                ),
            )
            conn.commit()
            position_id = int(cursor.lastrowid)
        return {
            "receipt_type": "paper_position",
            "position_id": position_id,
            "journal_id": int(journal_id),
            "journal_receipt_id": lineage.get("journal_receipt_id"),
            "symbol": clean_symbol,
            "side": clean_side,
            "entry_price": entry,
            "quantity": qty,
            "open_time": now,
            "current_price": entry,
            "unrealized_pnl_usd": pnl,
            "max_favorable_excursion": 0.0,
            "max_adverse_excursion": 0.0,
            "last_updated": now,
            "stop_loss": sl_value,
            "take_profit": tp_value,
            "evidence_hash": evidence_hash,
            "storage": "sqlite",
        }

    def update_position_levels(
        self,
        position_id: int,
        *,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        reason: str = "",
        source_id: str = "",
    ) -> dict[str, Any]:
        """Adjust an OPEN position's stop_loss / take_profit and audit every change."""
        self.init_db()
        position = self.get_position(int(position_id))
        if not position:
            raise ValueError(f"position_id {position_id} does not exist")
        now = utc_now().isoformat()
        changes: list[dict[str, Any]] = []
        updates: dict[str, float] = {}
        for field, new in (("stop_loss", stop_loss), ("take_profit", take_profit)):
            if new in (None, ""):
                continue
            new_val = float(new)
            old_raw = position.get(field)
            old_val = float(old_raw) if old_raw not in (None, "") else None
            if old_val is not None and old_val == new_val:
                continue  # no-op
            updates[field] = new_val
            changes.append({"field": field, "old": old_val, "new": new_val})
        if not updates:
            return {"position_id": int(position_id), "changed": [], "no_change": True}
        set_clause = ", ".join(f"{f} = ?" for f in updates)
        with connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE paper_positions SET {set_clause}, last_updated = ? WHERE position_id = ?",
                (*updates.values(), now, int(position_id)),
            )
            for ch in changes:
                conn.execute(
                    "INSERT INTO position_adjustments "
                    "(position_id, journal_id, field, old_value, new_value, reason, source_id, adjusted_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (int(position_id), int(position["journal_id"]), ch["field"],
                     ch["old"], ch["new"], reason, source_id, now),
                )
            conn.commit()
        return {"position_id": int(position_id), "journal_id": int(position["journal_id"]),
                "changed": changes, "adjusted_at": now}

    def update_positions(self, current_prices_dict: dict[str, float]) -> list[dict[str, Any]]:
        self.init_db()
        prices = {_clean_symbol(symbol): float(price) for symbol, price in dict(current_prices_dict or {}).items()}
        updated_at = utc_now().isoformat()
        updated_rows: list[dict[str, Any]] = []
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT position_id, journal_id, journal_receipt_id, symbol, side,
                       entry_price, quantity, open_time, current_price,
                       unrealized_pnl_usd, max_favorable_excursion,
                       max_adverse_excursion, last_updated, stop_loss, take_profit,
                       evidence_hash
                FROM paper_positions
                ORDER BY position_id ASC
                """
            ).fetchall()
            for row in rows:
                symbol = _clean_symbol(str(row["symbol"]))
                if symbol not in prices:
                    continue
                current_price = _positive_float(prices[symbol], label=f"price for {symbol}")
                pnl = pnl_for(
                    side=str(row["side"]),
                    entry_price=float(row["entry_price"]),
                    current_price=current_price,
                    quantity=float(row["quantity"]),
                )
                max_favorable = max(float(row["max_favorable_excursion"] or 0.0), pnl)
                max_adverse = min(float(row["max_adverse_excursion"] or 0.0), pnl)
                conn.execute(
                    """
                    UPDATE paper_positions
                    SET current_price = ?, unrealized_pnl_usd = ?, max_favorable_excursion = ?,
                        max_adverse_excursion = ?, last_updated = ?
                    WHERE position_id = ?
                    """,
                    (current_price, pnl, max_favorable, max_adverse, updated_at, int(row["position_id"])),
                )
                updated = record_from_row(row)
                updated.update(
                    {
                        "current_price": current_price,
                        "unrealized_pnl_usd": pnl,
                        "max_favorable_excursion": max_favorable,
                        "max_adverse_excursion": max_adverse,
                        "last_updated": updated_at,
                    }
                )
                updated_rows.append(updated)
            conn.commit()
        return updated_rows

    def close_position(self, position_id: int, exit_price: float, exit_reason: str) -> dict[str, Any]:
        position = self.get_position(int(position_id))
        if not position:
            raise ValueError(f"position_id {position_id} does not exist")
        reason = normalize_key(exit_reason)
        if reason not in VALID_EXIT_REASONS:
            raise ValueError("exit_reason must be tp, sl, or manual")
        exit_value = _positive_float(exit_price, label="exit_price")
        realized = pnl_for(
            side=str(position["side"]),
            entry_price=float(position["entry_price"]),
            current_price=exit_value,
            quantity=float(position["quantity"]),
        )
        max_favorable = max(float(position["max_favorable_excursion"] or 0.0), realized)
        max_adverse = min(float(position["max_adverse_excursion"] or 0.0), realized)
        exit_time = utc_now().isoformat()
        evidence_hash = outcome_evidence_hash_for(
            journal_id=int(position["journal_id"]),
            position_id=int(position_id),
            symbol=str(position["symbol"]),
            side=str(position["side"]),
            entry_price=float(position["entry_price"]),
            exit_price=exit_value,
            quantity=float(position["quantity"]),
            realized_pnl_usd=realized,
            entry_time=str(position["open_time"]),
            exit_time=exit_time,
            exit_reason=reason,
        )
        timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
        uid = uuid.uuid4().hex
        symbol_slug = slugify(str(position["symbol"]).replace("/", "_"), fallback="symbol")
        receipt_id = f"paper_outcome_{symbol_slug}_{timestamp}_{uid[:8]}"
        with connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO paper_outcomes (
                    receipt_id, position_id, journal_id, journal_receipt_id,
                    symbol, side, entry_price, exit_price, quantity,
                    realized_pnl_usd, pnl_usd, entry_time, exit_time, exit_reason,
                    max_favorable_excursion, max_adverse_excursion, evidence_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id, int(position_id), int(position["journal_id"]),
                    position.get("journal_receipt_id"), position["symbol"], position["side"],
                    float(position["entry_price"]), exit_value, float(position["quantity"]),
                    realized, realized, position["open_time"], exit_time, reason,
                    max_favorable, max_adverse, evidence_hash,
                ),
            )
            outcome_id = int(cursor.lastrowid)
            conn.execute("DELETE FROM paper_positions WHERE position_id = ?", (int(position_id),))
            conn.commit()
        return {
            "receipt_type": "paper_outcome",
            "receipt_id": receipt_id,
            "outcome_id": outcome_id,
            "position_id": int(position_id),
            "journal_id": int(position["journal_id"]),
            "journal_receipt_id": position.get("journal_receipt_id"),
            "symbol": position["symbol"],
            "side": position["side"],
            "entry_price": float(position["entry_price"]),
            "exit_price": exit_value,
            "quantity": float(position["quantity"]),
            "realized_pnl_usd": realized,
            "pnl_usd": realized,
            "entry_time": position["open_time"],
            "exit_time": exit_time,
            "exit_reason": reason,
            "max_favorable_excursion": max_favorable,
            "max_adverse_excursion": max_adverse,
            "evidence_hash": evidence_hash,
            "storage": "sqlite",
        }

    def close_position_by_journal(self, journal_id: int, exit_price: float, exit_reason: str) -> dict[str, Any]:
        position = self.position_for_journal(int(journal_id))
        if not position:
            raise ValueError(f"open paper position for journal_id {journal_id} does not exist")
        return self.close_position(int(position["position_id"]), exit_price=exit_price, exit_reason=exit_reason)

    def get_open_positions(self) -> list[dict[str, Any]]:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT position_id, journal_id, journal_receipt_id, symbol, side,
                       entry_price, quantity, open_time, current_price,
                       unrealized_pnl_usd, max_favorable_excursion,
                       max_adverse_excursion, last_updated, stop_loss, take_profit,
                       evidence_hash
                FROM paper_positions
                ORDER BY position_id ASC
                """
            ).fetchall()
        return [record_from_row(row) for row in rows]

    def get_recent_outcomes(self, *, limit: int = 100) -> list[dict[str, Any]]:
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT outcome_id, receipt_id, position_id, journal_id,
                       journal_receipt_id, symbol, side, entry_price, exit_price,
                       quantity, realized_pnl_usd, pnl_usd, entry_time, exit_time,
                       exit_reason, max_favorable_excursion, max_adverse_excursion,
                       evidence_hash
                FROM paper_outcomes
                ORDER BY outcome_id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [record_from_row(row) for row in rows]

    def get_closed_outcomes_with_source(
        self, *, since: str | None = None
    ) -> list[dict[str, Any]]:
        """Closed paper outcomes joined to their journal's source, for scoreboard builders.

        Pure data access (the store's job): returns one row per closed outcome with the
        originating ``source_id`` / ``source_type`` and, when ``raw_events`` carries it, the
        ``duplicate_of_event_id`` marker — so a market adapter can apply its own corruption
        / dedup filters and per-setup aggregation without reaching into SQL itself. No market
        judgement is made here; that lives in ``adapters/market``.
        """
        self.init_db()
        with connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            has_raw = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='raw_events'"
            ).fetchone() is not None
            duplicate_select = (
                "r.duplicate_of_event_id AS duplicate_of_event_id"
                if has_raw else "NULL AS duplicate_of_event_id"
            )
            raw_join = "LEFT JOIN raw_events r ON r.event_id = j.event_id" if has_raw else ""
            time_filter = "AND o.exit_time >= :since" if since else ""
            rows = conn.execute(
                f"""
                SELECT
                    j.source_id   AS source_id,
                    j.source_type AS source_type,
                    o.symbol      AS symbol,
                    o.side        AS side,
                    o.entry_price AS entry_price,
                    o.exit_price  AS exit_price,
                    o.pnl_usd     AS pnl_usd,
                    o.exit_reason AS exit_reason,
                    o.exit_time   AS exit_time,
                    {duplicate_select}
                FROM paper_outcomes o
                JOIN paper_journal j ON j.journal_id = o.journal_id
                {raw_join}
                WHERE 1=1 {time_filter}
                """,
                {"since": since} if since else {},
            ).fetchall()
        return [record_from_row(row) for row in rows]

    def simulate_exits(
        self,
        current_prices_dict: dict[str, float],
        *,
        take_profit_pct: float = 2.0,
        stop_loss_pct: float = 1.0,
        trailing_stop_pct: float | None = None,
        max_hold_hours: float | None = None,
    ) -> list[dict[str, Any]]:
        updated = self.update_positions(current_prices_dict)
        closed: list[dict[str, Any]] = []
        tp = max(0.0, float(take_profit_pct or 0.0)) / 100.0
        sl = max(0.0, float(stop_loss_pct or 0.0)) / 100.0
        trailing = max(0.0, float(trailing_stop_pct or 0.0)) / 100.0
        max_hold = max(0.0, float(max_hold_hours or 0.0))
        now = utc_now()
        for position in updated:
            entry = float(position["entry_price"])
            current = float(position["current_price"])
            quantity = float(position["quantity"])
            side = str(position["side"])
            pos_sl = position.get("stop_loss")
            pos_tp = position.get("take_profit")
            current_pnl = float(position.get("unrealized_pnl_usd") or 0.0)
            max_favorable = float(position.get("max_favorable_excursion") or 0.0)
            notional = entry * quantity
            max_favorable_return = (max_favorable / notional) if notional > 0 else 0.0
            trail_giveback = ((max_favorable - current_pnl) / notional) if notional > 0 else 0.0
            age_hours = 0.0
            if max_hold > 0:
                try:
                    opened = datetime.fromisoformat(str(position["open_time"]).replace("Z", "+00:00"))
                    if opened.tzinfo is None:
                        opened = opened.replace(tzinfo=UTC)
                    age_hours = max(0.0, (now - opened.astimezone(UTC)).total_seconds() / 3600.0)
                except (TypeError, ValueError):
                    age_hours = 0.0
            if side == "long":
                change = (current - entry) / entry
                hit_fixed_tp = current >= float(pos_tp) if pos_tp else (tp > 0 and trailing <= 0 and change >= tp)
                hit_sl = current <= float(pos_sl) if pos_sl else (sl > 0 and change <= -sl)
            else:
                change = (entry - current) / entry
                hit_fixed_tp = current <= float(pos_tp) if pos_tp else (tp > 0 and trailing <= 0 and change >= tp)
                hit_sl = current >= float(pos_sl) if pos_sl else (sl > 0 and change <= -sl)
            hit_trailing_tp = trailing > 0 and tp > 0 and max_favorable_return >= tp and trail_giveback >= trailing
            hit_max_hold = max_hold > 0 and age_hours >= max_hold
            if hit_fixed_tp or hit_trailing_tp:
                closed.append(self.close_position(int(position["position_id"]), current, "tp"))
            elif hit_sl:
                closed.append(self.close_position(int(position["position_id"]), current, "sl"))
            elif hit_max_hold:
                closed.append(self.close_position(int(position["position_id"]), current, "manual"))
        return closed

    def get_portfolio_summary(self) -> dict[str, Any]:
        self.init_db()
        outcomes = self.get_recent_outcomes(limit=100000)
        positions = self.get_open_positions()
        pnl_values = [float(row.get("realized_pnl_usd") or row.get("pnl_usd") or 0.0) for row in outcomes]
        wins = [value for value in pnl_values if value > 0]
        losses = [value for value in pnl_values if value < 0]
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        win_rate = (len(wins) / len(pnl_values)) if pnl_values else None
        if gross_loss > 0:
            profit_factor: float | None = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = float("inf")
        else:
            profit_factor = None

        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for value in reversed(pnl_values):
            cumulative += value
            peak = max(peak, cumulative)
            max_drawdown = max(max_drawdown, peak - cumulative)

        sharpe = 0.0
        if len(pnl_values) >= 2:
            stdev = statistics.pstdev(pnl_values)
            if stdev > 0:
                sharpe = statistics.mean(pnl_values) / stdev

        unrealized = sum(float(row.get("unrealized_pnl_usd") or 0.0) for row in positions)
        latest = outcomes[0] if outcomes else None
        return {
            "trade_count": len(pnl_values),
            "closed_trade_count": len(pnl_values),
            "open_position_count": len(positions),
            "total_realized_pnl_usd": round(sum(pnl_values), 8),
            "unrealized_pnl_usd": round(unrealized, 8),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": None if win_rate is None else round(win_rate, 8),
            "profit_factor": profit_factor if profit_factor == float("inf") else (
                None if profit_factor is None else round(profit_factor, 8)
            ),
            "max_drawdown_usd": round(max_drawdown, 8),
            "sharpe": round(sharpe, 8),
            "latest_outcome_receipt_id": latest.get("receipt_id") if latest else "",
            "db_path": str(self.db_path),
        }

    def audit_summary(self) -> dict[str, Any]:
        summary = self.get_portfolio_summary()
        summary["latest_outcomes"] = self.get_recent_outcomes(limit=5)
        summary["open_positions"] = self.get_open_positions()[:20]
        return summary
