"""Safe public FoxClaw Hunt export contracts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from foxclaw.adapters.event_contracts.kalshi.models import payload_hash
from foxclaw.adapters.event_contracts.markets import to_jsonable

PRIVATE_FIELDS = {
    "dossier_hash",
    "source_receipt_hash",
    "receipt_json",
    "raw_payload_hash",
    "archived_path",
    "request_json",
    "response_json",
}


def public_forecast(item: Mapping[str, Any], *, supersedes: str | None = None) -> dict[str, Any]:
    public = {
        "market_id": item.get("market_id"),
        "side": item.get("side"),
        "verdict": item.get("verdict", "paper"),
        "mode": "PAPER",
        "independent_probability": item.get("independent_probability"),
        "market_probability": item.get("market_probability"),
        "usable_edge": item.get("usable_edge"),
        "resolved_outcome": item.get("resolved_outcome"),
        "net_result": item.get("net_result"),
        "status": item.get("status", "open"),
        "supersedes": supersedes or item.get("supersedes"),
    }
    cleaned = {key: to_jsonable(value) for key, value in public.items() if value is not None}
    cleaned["public_id"] = payload_hash(cleaned)
    return cleaned


def build_public_export(
    forecasts: list[Mapping[str, Any]],
    *,
    scoreboard: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    public_items = [public_forecast(item) for item in forecasts]
    payload = {
        "mode": "PAPER",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "forecasts": public_items,
        "scoreboard": dict(scoreboard or {}),
    }
    payload["export_hash"] = payload_hash(payload)
    return payload


def write_public_export(export: Mapping[str, Any], output_dir: str | Path) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    forecasts_json = out / "public_forecasts.json"
    forecasts_md = out / "public_forecasts.md"
    scoreboard_json = out / "scoreboard.json"
    scoreboard_md = out / "scoreboard.md"
    build_log = out / "build_log.json"
    forecasts_json.write_text(json.dumps(export, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    scoreboard_json.write_text(
        json.dumps(export.get("scoreboard", {}), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    forecasts_md.write_text(_forecasts_md(export), encoding="utf-8")
    scoreboard_md.write_text(_scoreboard_md(export.get("scoreboard", {})), encoding="utf-8")
    build_log.write_text(
        json.dumps({"mode": "PAPER", "export_hash": export.get("export_hash")}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "public_forecasts_json": forecasts_json,
        "public_forecasts_md": forecasts_md,
        "scoreboard_json": scoreboard_json,
        "scoreboard_md": scoreboard_md,
        "build_log": build_log,
    }


def assert_no_private_fields(export: Mapping[str, Any]) -> None:
    blob = json.dumps(export, sort_keys=True)
    for field in PRIVATE_FIELDS:
        if field in blob:
            raise ValueError(f"private/internal field leaked into public export: {field}")


def _forecasts_md(export: Mapping[str, Any]) -> str:
    lines = ["# FoxClaw Hunt Forecasts", "", f"Mode: `{export.get('mode')}`", ""]
    for item in export.get("forecasts", []):
        lines.append(f"- `{item.get('market_id')}` {item.get('side')} -> {item.get('verdict')} ({item.get('status', 'open')})")
    return "\n".join(lines) + "\n"


def _scoreboard_md(scoreboard: Mapping[str, Any]) -> str:
    lines = ["# FoxClaw Hunt Scoreboard", ""]
    for key, value in sorted(scoreboard.items()):
        lines.append(f"- `{key}`: {value}")
    return "\n".join(lines) + "\n"
