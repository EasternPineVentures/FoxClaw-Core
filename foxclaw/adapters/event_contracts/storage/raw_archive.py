"""Gzip JSONL archive for raw Forecast Desk responses."""

from __future__ import annotations

import gzip
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from foxclaw.adapters.event_contracts.kalshi.models import payload_hash

from .db import REPO_ROOT, reject_cloud_sync_path

FORECAST_RAW_ENV = "FOXCLAW_FORECAST_RAW_DIR"


@dataclass(frozen=True)
class RawArchiveReceipt:
    raw_hash: str
    archive_path: Path
    endpoint: str
    observed_at: str


def resolve_raw_dir(raw_dir: str | Path | None = None, *, project_root: str | Path | None = None) -> Path:
    if raw_dir is not None:
        path = Path(raw_dir).expanduser().resolve()
    elif os.environ.get(FORECAST_RAW_ENV):
        path = Path(os.environ[FORECAST_RAW_ENV]).expanduser().resolve()
    elif project_root is not None:
        path = (Path(project_root).expanduser().resolve() / "data" / "forecast_raw")
    else:
        path = REPO_ROOT / "data" / "forecast_raw"
    reject_cloud_sync_path(path)
    return path


def append_raw_response(
    *,
    raw_dir: str | Path | None,
    endpoint: str,
    payload: Mapping[str, Any],
    request: Mapping[str, Any] | None = None,
    observed_at: datetime | None = None,
) -> RawArchiveReceipt:
    observed = (observed_at or datetime.now(UTC)).astimezone(UTC)
    raw_hash = payload_hash(payload)
    target_dir = resolve_raw_dir(raw_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    archive_path = target_dir / f"{observed:%Y%m%d}.jsonl.gz"
    record = {
        "raw_hash": raw_hash,
        "endpoint": endpoint,
        "request": dict(request or {}),
        "observed_at": observed.isoformat().replace("+00:00", "Z"),
        "payload": payload,
    }
    with gzip.open(archive_path, "at", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return RawArchiveReceipt(
        raw_hash=raw_hash,
        archive_path=archive_path,
        endpoint=endpoint,
        observed_at=record["observed_at"],
    )


def iter_raw_records(path: str | Path) -> Iterable[Mapping[str, Any]]:
    with gzip.open(Path(path), "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                loaded = json.loads(line)
                if not isinstance(loaded, Mapping):
                    raise TypeError("raw archive record must be a JSON object")
                yield loaded
