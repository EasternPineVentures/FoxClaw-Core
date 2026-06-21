"""Offline parser-admission policy for v13 compatibility receipts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import foxclaw.adapters.market.signals.reason_codes as reason_codes

ADMISSION_POLICY_VERSION = "parser_admission_v0"


@dataclass(frozen=True)
class ParserAdmissionDecision:
    accepted: bool
    reason_code: str
    diagnostic_category: str | None
    retryable: bool
    field_warnings: tuple[str, ...]


REQUIRED_FIELDS = (
    "candidate_type",
    "symbol",
    "side",
    "entry_price",
    "stop_loss",
    "take_profit",
)

MISSING_REASON_BY_FIELD = {
    "symbol": reason_codes.MISSING_SYMBOL,
    "side": reason_codes.MISSING_SIDE,
    "entry_price": reason_codes.MISSING_ENTRY,
    "stop_loss": reason_codes.MISSING_STOP,
    "take_profit": reason_codes.MISSING_TARGET,
}


def evaluate_parser_admission(
    normalized_payload: Mapping[str, Any],
    *,
    pre_rejection_reason: str | None = None,
) -> ParserAdmissionDecision:
    """Admit only complete trade signals; keep parser confidence separate."""
    if pre_rejection_reason:
        return _reject(pre_rejection_reason)

    for field in REQUIRED_FIELDS:
        value = normalized_payload.get(field)
        if value is None or value == "":
            return _reject(MISSING_REASON_BY_FIELD.get(field, reason_codes.MALFORMED_PAYLOAD))

    return ParserAdmissionDecision(
        accepted=True,
        reason_code=reason_codes.ACCEPTED_TRADE_SIGNAL,
        diagnostic_category=None,
        retryable=False,
        field_warnings=(),
    )


def _reject(reason_code: str) -> ParserAdmissionDecision:
    retryable = reason_code not in {
        reason_codes.PROMPT_INJECTION_ATTEMPT,
        reason_codes.DUPLICATE_CONTENT_SOURCE,
        reason_codes.CONTEXT_ONLY,
    }
    return ParserAdmissionDecision(
        accepted=False,
        reason_code=reason_code,
        diagnostic_category=reason_codes.diagnostic_category(reason_code),
        retryable=retryable,
        field_warnings=(reason_code,),
    )
