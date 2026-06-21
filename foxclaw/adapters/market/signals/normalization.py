"""Deterministic normalization utilities for offline v13 parser compatibility."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import hashlib
import re
from typing import Any, Iterable, Mapping

ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200f\ufeff]")
WHITESPACE_RE = re.compile(r"\s+")
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])(\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)([kKmM]?)")

SYMBOL_ALIASES = {
    "BTC": "BTC/USD",
    "BTCUSD": "BTC/USD",
    "BTCUSDT": "BTC/USD",
    "BITCOIN": "BTC/USD",
    "ETH": "ETH/USD",
    "ETHUSD": "ETH/USD",
    "ETHUSDT": "ETH/USD",
    "ETHEREUM": "ETH/USD",
    "SOL": "SOL/USD",
    "SOLUSD": "SOL/USD",
    "SOLUSDT": "SOL/USD",
    "SPY": "SPY",
    "QQQ": "QQQ",
}


def normalize_message_text(value: str) -> str:
    """Collapse sanitized message text into the source-scoped dedup form."""
    text = ZERO_WIDTH_RE.sub("", str(value or ""))
    text = text.replace("\r", "\n")
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip().lower()


def content_hash_for_text(text: str) -> str:
    """Hash normalized message content without source identity."""
    normalized = normalize_message_text(text)
    digest = hashlib.sha256(
        ("foxclaw.parser_v13.normalized_content\n" + normalized).encode("utf-8")
    ).hexdigest()
    return "sha256:" + digest


def dedupe_key_for(*, source_id: str, content_hash: str) -> str:
    """Hash the v13 dedup key: normalized content hash plus source id."""
    digest = hashlib.sha256(
        (
            "foxclaw.parser_v13.source_scoped_dedupe\n"
            + str(source_id or "")
            + "\n"
            + str(content_hash or "")
        ).encode("utf-8")
    ).hexdigest()
    return "sha256:" + digest


def extract_sanitized_text(envelope: Mapping[str, Any]) -> str:
    """Return committed-safe text from a replay envelope without raw lineage."""
    message = envelope.get("sanitized_message")
    if not isinstance(message, Mapping):
        raw = envelope.get("raw_source_event")
        if isinstance(raw, Mapping):
            content = raw.get("content")
            if isinstance(content, Mapping):
                return str(content.get("content_excerpt") or "")
        return ""

    parts: list[str] = [str(message.get("body") or "")]
    parts.extend(_embed_parts(message.get("embeds")))
    parts.extend(_image_parts(message.get("image_metadata")))
    return "\n".join(part for part in parts if part.strip())


def normalize_symbol(text: str) -> str | None:
    """Detect and normalize a supported market symbol."""
    upper = str(text or "").upper()
    for alias in sorted(SYMBOL_ALIASES, key=len, reverse=True):
        pattern = rf"(?<![A-Z0-9])\$?{re.escape(alias)}(?![A-Z0-9])"
        if re.search(pattern, upper):
            return SYMBOL_ALIASES[alias]
    return None


def side_tokens(text: str) -> tuple[bool, bool]:
    """Return whether long/buy and short/sell intent tokens are present."""
    lower = normalize_message_text(text)
    long_seen = bool(re.search(r"\b(long|buy|bullish|calls?|upside)\b", lower))
    short_seen = bool(re.search(r"\b(short|sell|bearish|puts?|downside)\b", lower))
    return long_seen, short_seen


def normalize_side(text: str) -> str | None:
    """Normalize direction to long/short when unambiguous."""
    long_seen, short_seen = side_tokens(text)
    if long_seen and not short_seen:
        return "long"
    if short_seen and not long_seen:
        return "short"
    return None


def extract_decimal_after(text: str, labels: Iterable[str]) -> Decimal | None:
    """Find the first decimal value after one of the given rule labels."""
    lower = normalize_message_text(text)
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(
        rf"\b(?:{label_pattern})\b(?:\s*(?:at|around|near|=|:|@|below|above|to))?"
        rf"[^0-9]{{0,18}}"
        rf"(\d+(?:,\d{{3}})*(?:\.\d+)?|\.\d+)([km]?)",
        re.I,
    )
    match = pattern.search(lower)
    if match:
        return _decimal(match.group(1), match.group(2))
    return None


def extract_first_decimal(text: str) -> Decimal | None:
    """Return the first numeric token in sanitized text."""
    match = NUMBER_RE.search(str(text or ""))
    if not match:
        return None
    return decimal_from_token(match.group(1), match.group(2))


def decimal_from_token(number: str, suffix: str = "") -> Decimal | None:
    """Parse a v13-style decimal token, including k/m shorthand."""
    try:
        value = Decimal(str(number).replace(",", ""))
    except InvalidOperation:
        return None
    suffix = str(suffix or "").lower()
    if suffix == "k":
        value *= Decimal("1000")
    elif suffix == "m":
        value *= Decimal("1000000")
    return value


def canonical_decimal(value: Any) -> str | None:
    """Return a stable decimal string for parity comparison."""
    if value is None or isinstance(value, bool):
        return None
    try:
        decimal = Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None
    normalized = decimal.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f").rstrip("0").rstrip(".")


def decimal_to_json_number(value: Decimal | None) -> int | float | None:
    """Convert a Decimal to an int when exact, otherwise to a float."""
    if value is None:
        return None
    if value == value.to_integral():
        return int(value)
    return float(value)


def _decimal(number: str, suffix: str = "") -> Decimal | None:
    return decimal_from_token(number, suffix)


def _embed_parts(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    parts: list[str] = []
    for embed in value:
        if not isinstance(embed, Mapping):
            continue
        for key in ("title", "description"):
            if embed.get(key):
                parts.append(str(embed[key]))
        fields = embed.get("fields")
        if isinstance(fields, list):
            for field in fields:
                if isinstance(field, Mapping):
                    parts.append(str(field.get("name") or ""))
                    parts.append(str(field.get("value") or ""))
    return parts


def _image_parts(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    parts: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            parts.append(str(item.get("alt_text") or ""))
            parts.append(str(item.get("ocr_excerpt") or ""))
    return parts
