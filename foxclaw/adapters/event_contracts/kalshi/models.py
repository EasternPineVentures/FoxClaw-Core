"""Raw Kalshi response validators and fixed-point parsers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence


def payload_hash(payload: Mapping[str, Any] | Sequence[Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def require_mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def require_sequence(value: Any, *, label: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise TypeError(f"{label} must be an array")
    return value


def fixed_decimal(value: Any, *, label: str, minimum: Decimal | None = None,
                  maximum: Decimal | None = None) -> Decimal:
    """Parse a Kalshi fixed-point string into Decimal without accepting floats or bools."""

    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"{label} must be a fixed-point string or integer, got {type(value).__name__}")
    if isinstance(value, Decimal):
        dec = value
    elif isinstance(value, int):
        dec = Decimal(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError(f"{label} is empty")
        try:
            dec = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"{label} is not a valid fixed-point decimal: {value!r}") from exc
    else:
        raise TypeError(f"{label} must be a fixed-point string or integer, got {type(value).__name__}")
    if not dec.is_finite():
        raise ValueError(f"{label} must be finite, got {value!r}")
    if minimum is not None and dec < minimum:
        raise ValueError(f"{label} must be >= {minimum}, got {value!r}")
    if maximum is not None and dec > maximum:
        raise ValueError(f"{label} must be <= {maximum}, got {value!r}")
    return dec


def optional_fixed_decimal(value: Any, *, label: str, minimum: Decimal | None = None,
                           maximum: Decimal | None = None) -> Decimal | None:
    if value is None or value == "":
        return None
    return fixed_decimal(value, label=label, minimum=minimum, maximum=maximum)


def parse_datetime_utc(value: Any, *, label: str) -> datetime | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise TypeError(f"{label} must be an ISO timestamp string")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} is not a valid ISO timestamp: {value!r}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def extract_items(payload: Mapping[str, Any], collection_key: str) -> list[Mapping[str, Any]]:
    require_mapping(payload, label="payload")
    raw_items = payload.get(collection_key)
    if raw_items is None:
        raise KeyError(f"payload missing collection key {collection_key!r}")
    seq = require_sequence(raw_items, label=collection_key)
    out: list[Mapping[str, Any]] = []
    for idx, item in enumerate(seq):
        out.append(require_mapping(item, label=f"{collection_key}[{idx}]"))
    return out


def settlement_source_strings(raw_sources: Any) -> tuple[str, ...]:
    if raw_sources in (None, ""):
        return ()
    seq = require_sequence(raw_sources, label="settlement_sources")
    out: list[str] = []
    for idx, item in enumerate(seq):
        if isinstance(item, str):
            text = item.strip()
        else:
            src = require_mapping(item, label=f"settlement_sources[{idx}]")
            name = str(src.get("name") or "").strip()
            url = str(src.get("url") or "").strip()
            text = " | ".join(part for part in (name, url) if part)
        if text:
            out.append(text)
    return tuple(out)
