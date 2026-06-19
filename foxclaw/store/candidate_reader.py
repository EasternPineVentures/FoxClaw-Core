"""Read-only accepted-candidate access for private Microscope assessments."""
from __future__ import annotations

from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Iterator

SQLITE_TIMEOUT_S = 30
SQLITE_BUSY_TIMEOUT_MS = 30000

ACCEPTED_CANDIDATE_COLUMNS = (
    "candidate_id",
    "candidate_uid",
    "receipt_id",
    "event_id",
    "attempt_id",
    "source_id",
    "source_type",
    "parser_version",
    "candidate_type",
    "normalized_payload_json",
    "confidence",
    "admission_policy_version",
    "admission_reason",
    "status",
    "created_at",
    "evidence_hash",
)


class CandidateReaderError(RuntimeError):
    """Base error for read-only candidate access."""


class CandidateDatabaseMissingError(CandidateReaderError):
    """Raised when the requested Grove database path does not exist."""


class CandidateDatabaseError(CandidateReaderError):
    """Raised when an existing path is not a usable SQLite database."""


class CandidateSchemaError(CandidateReaderError):
    """Raised when the database does not expose the expected candidate schema."""


def readonly_uri_for(db_path: str | Path) -> str:
    """Build a Windows-safe SQLite read-only URI for an existing database path."""
    path = Path(db_path).expanduser().resolve()
    return f"{path.as_uri()}?mode=ro"


@contextmanager
def connect_readonly(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Open SQLite with URI ``mode=ro`` and ``PRAGMA query_only=ON``."""
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        raise CandidateDatabaseMissingError(f"database does not exist: {path}")
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(readonly_uri_for(path), uri=True, timeout=SQLITE_TIMEOUT_S)
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
        conn.execute("PRAGMA query_only = ON")
        yield conn
    except sqlite3.DatabaseError as exc:
        if conn is None:
            raise CandidateDatabaseError(f"invalid SQLite database: {path}") from exc
        raise
    finally:
        if conn is not None:
            conn.close()


class ReadOnlyCandidateReader:
    """Read accepted candidates without invoking any DDL-capable store path."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).expanduser().resolve()

    def get_candidate(self, candidate_id: int) -> dict[str, object] | None:
        """Return one accepted candidate by id, or ``None`` when absent/not accepted."""
        with connect_readonly(self.db_path) as conn:
            _ensure_candidate_schema(conn)
            row = conn.execute(
                f"""
                SELECT {", ".join(ACCEPTED_CANDIDATE_COLUMNS)}
                FROM accepted_candidates
                WHERE candidate_id = ? AND status = 'accepted'
                """,
                (int(candidate_id),),
            ).fetchone()
        return _record_from_row(row)

    def iter_after(self, *, candidate_id: int = 0, limit: int = 100) -> list[dict[str, object]]:
        """Return accepted candidates ordered after ``candidate_id`` for later batch use."""
        bounded_limit = max(1, min(int(limit), 1000))
        with connect_readonly(self.db_path) as conn:
            _ensure_candidate_schema(conn)
            rows = conn.execute(
                f"""
                SELECT {", ".join(ACCEPTED_CANDIDATE_COLUMNS)}
                FROM accepted_candidates
                WHERE candidate_id > ? AND status = 'accepted'
                ORDER BY candidate_id ASC
                LIMIT ?
                """,
                (int(candidate_id), bounded_limit),
            ).fetchall()
        return [_record_from_row(row) for row in rows if row is not None]


def _ensure_candidate_schema(conn: sqlite3.Connection) -> None:
    try:
        table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='accepted_candidates'"
        ).fetchone()
        if table is None:
            raise CandidateSchemaError("accepted_candidates table is missing")
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(accepted_candidates)")}
    except sqlite3.DatabaseError as exc:
        raise CandidateDatabaseError("database cannot be inspected as SQLite") from exc
    missing = set(ACCEPTED_CANDIDATE_COLUMNS) - columns
    if missing:
        raise CandidateSchemaError(
            "accepted_candidates missing columns: " + ", ".join(sorted(missing))
        )


def _record_from_row(row: sqlite3.Row | None) -> dict[str, object] | None:
    if row is None:
        return None
    return {key: row[key] for key in ACCEPTED_CANDIDATE_COLUMNS}
