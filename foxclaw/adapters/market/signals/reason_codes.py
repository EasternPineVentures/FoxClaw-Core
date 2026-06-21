"""Reason-code vocabulary for the offline v13 parser compatibility layer."""
from __future__ import annotations

ACCEPTED_TRADE_SIGNAL = "accepted_trade_signal"
CONTEXT_ONLY = "context_only"
MALFORMED_PAYLOAD = "malformed_payload"
MISSING_SYMBOL = "missing_symbol"
MISSING_SIDE = "missing_side"
MISSING_ENTRY = "missing_entry"
MISSING_STOP = "missing_stop"
MISSING_TARGET = "missing_target"
UNSUPPORTED_SYMBOL = "unsupported_symbol"
AMBIGUOUS_DIRECTION = "ambiguous_direction"
PROMPT_INJECTION_ATTEMPT = "prompt_injection_attempt"
DUPLICATE_CONTENT_SOURCE = "duplicate_content_source"

REJECTION_CATEGORY_BY_REASON = {
    CONTEXT_ONLY: "context_only",
    MALFORMED_PAYLOAD: "malformed_payload",
    MISSING_SYMBOL: "missing_required_field",
    MISSING_SIDE: "missing_required_field",
    MISSING_ENTRY: "missing_required_field",
    MISSING_STOP: "missing_required_field",
    MISSING_TARGET: "missing_required_field",
    UNSUPPORTED_SYMBOL: "unsupported_symbol",
    AMBIGUOUS_DIRECTION: "ambiguous_direction",
    PROMPT_INJECTION_ATTEMPT: "security_rejected",
    DUPLICATE_CONTENT_SOURCE: "duplicate",
}

SAFE_DIAGNOSTIC_BY_REASON = {
    CONTEXT_ONLY: "content did not contain an actionable trade setup",
    MALFORMED_PAYLOAD: "structured parser output was malformed",
    MISSING_SYMBOL: "required symbol field was not detected",
    MISSING_SIDE: "required side field was not detected",
    MISSING_ENTRY: "required entry field was not detected",
    MISSING_STOP: "required stop field was not detected",
    MISSING_TARGET: "required target field was not detected",
    UNSUPPORTED_SYMBOL: "detected symbol is not in the supported compatibility set",
    AMBIGUOUS_DIRECTION: "direction was ambiguous",
    PROMPT_INJECTION_ATTEMPT: "message contained parser-instruction-like text",
    DUPLICATE_CONTENT_SOURCE: "source-scoped normalized content duplicate",
}


def diagnostic_category(reason_code: str) -> str:
    """Return the contract diagnostic category for a parser reason code."""
    return REJECTION_CATEGORY_BY_REASON.get(str(reason_code), "policy_rejected")


def safe_diagnostic(reason_code: str) -> str:
    """Return a private-value-free diagnostic for reports and ParserRejection."""
    return SAFE_DIAGNOSTIC_BY_REASON.get(str(reason_code), "parser rejected the event")
