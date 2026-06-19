"""Read-only market outcome evidence for private Microscope assessments."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .candidate_reader import CandidateDatabaseError, CandidateSchemaError, connect_readonly

MARKET_OUTCOME_COLUMNS = (
    "source_id",
    "source_type",
    "symbol",
    "side",
    "entry_price",
    "exit_price",
    "pnl_usd",
    "exit_reason",
    "exit_time",
    "duplicate_of_event_id",
)


class ReadOnlyMarketEvidenceReader:
    """Read closed paper outcomes through a query-only SQLite connection."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).expanduser().resolve()

    def get_closed_outcomes_with_source(self, *, since: str | None = None) -> list[dict[str, Any]]:
        """Return closed paper outcomes joined to source metadata, without writes."""
        with connect_readonly(self.db_path) as conn:
            _ensure_outcome_schema(conn)
            has_raw = _table_exists(conn, "raw_events")
            duplicate_select = (
                "r.duplicate_of_event_id AS duplicate_of_event_id"
                if has_raw
                else "NULL AS duplicate_of_event_id"
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
        return [{key: row[key] for key in MARKET_OUTCOME_COLUMNS} for row in rows]


def _ensure_outcome_schema(conn: sqlite3.Connection) -> None:
    try:
        missing_tables = [
            name for name in ("paper_outcomes", "paper_journal") if not _table_exists(conn, name)
        ]
    except sqlite3.DatabaseError as exc:
        raise CandidateDatabaseError("database cannot be inspected as SQLite") from exc
    if missing_tables:
        raise CandidateSchemaError("missing outcome tables: " + ", ".join(missing_tables))


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        is not None
    )
