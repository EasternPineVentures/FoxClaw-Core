"""Offline market-signal parser compatibility helpers."""
from __future__ import annotations

from .reason_codes import ACCEPTED_TRADE_SIGNAL
from .legacy_v13 import (
    PARSER_NAME,
    PARSER_VERSION,
    ParserCompatResult,
    parse_raw_source_event,
)
from .normalization import (
    canonical_decimal,
    content_hash_for_text,
    dedupe_key_for,
    normalize_message_text,
)

__all__ = [
    "ACCEPTED_TRADE_SIGNAL",
    "PARSER_NAME",
    "PARSER_VERSION",
    "ParserCompatResult",
    "canonical_decimal",
    "content_hash_for_text",
    "dedupe_key_for",
    "normalize_message_text",
    "parse_raw_source_event",
]
