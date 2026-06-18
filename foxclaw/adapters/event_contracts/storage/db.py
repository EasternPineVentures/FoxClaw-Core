"""Forecast Desk database resolution and SQLite helpers."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
FORECAST_DB_ENV = "FOXCLAW_FORECAST_DB"
SQLITE_TIMEOUT_S = 30
SQLITE_BUSY_TIMEOUT_MS = 30000

_CLOUD_SYNC_MARKERS = {
    "onedrive",
    "google drive",
    "dropbox",
    "icloud",
}


def resolve_forecast_db(
    db_path: str | Path | None = None,
    *,
    project_root: str | Path | None = None,
) -> Path:
    """Locate `forecast_desk.db` without using a cloud-sync source of truth."""

    if db_path is not None:
        path = Path(db_path).expanduser().resolve()
    elif os.environ.get(FORECAST_DB_ENV):
        path = Path(os.environ[FORECAST_DB_ENV]).expanduser().resolve()
    elif project_root is not None:
        path = (Path(project_root).expanduser().resolve() / "data" / "forecast_desk.db")
    else:
        path = REPO_ROOT / "data" / "forecast_desk.db"
    reject_cloud_sync_path(path)
    return path


def reject_cloud_sync_path(path: Path) -> None:
    lowered = str(path).lower()
    if any(marker in lowered for marker in _CLOUD_SYNC_MARKERS):
        raise ValueError(f"Forecast Desk DB must not live in a cloud-sync path: {path}")


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=SQLITE_TIMEOUT_S)
    conn.row_factory = sqlite3.Row
    conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
