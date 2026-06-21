"""Offline compatibility implementation for the active v13 rule parser."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from foxclaw.contract.internal import schema_path
from foxclaw.contract.public.schema_validation import validate_json_schema
from foxclaw.policy.parser_admission import ADMISSION_POLICY_VERSION, evaluate_parser_admission

from .normalization import (
    content_hash_for_text,
    decimal_from_token,
    decimal_to_json_number,
    dedupe_key_for,
    extract_decimal_after,
    extract_first_decimal,
    extract_sanitized_text,
    normalize_message_text,
    normalize_side,
    normalize_symbol,
    side_tokens,
)
from . import reason_codes

PARSER_NAME = "legacy_v13_rule_compat"
PARSER_VERSION = "live_raw_parser_admission_v13"
RESULT_SCHEMA_VERSION = "parser_compat_result.v0"

ENTRY_LABELS = ("entry", "entries", "enter", "at", "@", "above", "over")
STOP_LABELS = ("stop", "sl", "stop loss", "invalidation", "invalid")
TARGET_LABELS = ("target", "targets", "tp", "take profit", "profit")
QUANTITY_LABELS = ("qty", "quantity", "size")
PROMPT_INJECTION_RE = re.compile(
    r"\b(ignore previous|system prompt|developer message|reveal prompt|override instructions)\b",
    re.I,
)


@dataclass(frozen=True)
class ParserCompatResult:
    """In-memory parser compatibility result with private lineage kept internal."""

    raw_source_event: dict[str, Any]
    parse_attempt: dict[str, Any]
    accepted_candidate: dict[str, Any] | None
    parser_rejection: dict[str, Any] | None
    private_lineage: dict[str, Any]
    dedupe_key: str
    reason_code: str
    parser_confidence: int

    @property
    def accepted(self) -> bool:
        return self.accepted_candidate is not None

    @property
    def normalized_payload(self) -> dict[str, Any]:
        payload = self.parse_attempt.get("normalized_payload")
        return dict(payload) if isinstance(payload, Mapping) else {}

    def to_report_dict(self, *, fixture_id: str | None = None) -> dict[str, Any]:
        """Return a safe JSON object for CLI/stdout parity reporting."""
        payload = {
            "schema_version": RESULT_SCHEMA_VERSION,
            "fixture_id": fixture_id,
            "parser_name": PARSER_NAME,
            "parser_version": PARSER_VERSION,
            "accepted": self.accepted,
            "status": "accepted" if self.accepted else "rejected",
            "reason_code": self.reason_code,
            "parser_confidence": self.parser_confidence,
            "normalized_payload": self.normalized_payload,
            "parse_attempt": {
                "parse_attempt_id": self.parse_attempt["parse_attempt_id"],
                "raw_event_id": self.parse_attempt["raw_event_id"],
                "status": self.parse_attempt["status"],
                "reason_codes": list(self.parse_attempt["reason_codes"]),
            },
            "evidence_lineage": {
                "raw_event_id": self.parse_attempt["raw_event_id"],
                "parse_attempt_id": self.parse_attempt["parse_attempt_id"],
                "content_hash": self.raw_source_event["content"]["content_hash"],
                "source_scoped_dedupe": True,
            },
        }
        if self.accepted_candidate is not None:
            payload["accepted_candidate"] = {
                "accepted_candidate_id": self.accepted_candidate["accepted_candidate_id"],
                "candidate_type": self.accepted_candidate["candidate_type"],
                "parser_version": self.accepted_candidate["parser_version"],
                "admission_policy_version": self.accepted_candidate[
                    "admission_policy_version"
                ],
                "admission_reason": self.accepted_candidate["admission_reason"],
                "evidence_hash": self.accepted_candidate["evidence_hash"],
                "status": self.accepted_candidate["status"],
            }
        if self.parser_rejection is not None:
            payload["parser_rejection"] = {
                "parser_rejection_id": self.parser_rejection["parser_rejection_id"],
                "reason_code": self.parser_rejection["reason_code"],
                "diagnostic_category": self.parser_rejection["diagnostic_category"],
                "retryable": self.parser_rejection["retryable"],
                "safe_diagnostic": self.parser_rejection["safe_diagnostic"],
            }
        return payload


def parse_raw_source_event(
    envelope: Mapping[str, Any],
    *,
    mode: str = "offline_replay",
    generated_at: str | None = None,
) -> ParserCompatResult:
    """Parse one sanitized replay envelope without network or DB side effects."""
    raw = _raw_source_event(envelope)
    text = extract_sanitized_text(envelope)
    raw = _with_derived_dedupe(raw, text)
    validate_json_schema(raw, _schema("raw_source_event.schema.json"))

    now = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    normalized_payload, pre_rejection = _parse_payload(text)
    decision = evaluate_parser_admission(
        normalized_payload,
        pre_rejection_reason=pre_rejection,
    )
    confidence = _parser_confidence(normalized_payload, decision.accepted)
    parse_attempt = _parse_attempt(
        raw=raw,
        normalized_payload=normalized_payload,
        decision=decision,
        confidence=confidence,
        mode=mode,
        created_at=now,
    )
    validate_json_schema(parse_attempt, _schema("parse_attempt.schema.json"))

    accepted_candidate: dict[str, Any] | None = None
    parser_rejection: dict[str, Any] | None = None
    if decision.accepted:
        accepted_candidate = _accepted_candidate(raw, parse_attempt, confidence, now)
        validate_json_schema(accepted_candidate, _schema("accepted_candidate.schema.json"))
    else:
        parser_rejection = _parser_rejection(raw, parse_attempt, decision, now)
        validate_json_schema(parser_rejection, _schema("parser_rejection.schema.json"))

    return ParserCompatResult(
        raw_source_event=raw,
        parse_attempt=parse_attempt,
        accepted_candidate=accepted_candidate,
        parser_rejection=parser_rejection,
        private_lineage=_private_lineage(envelope, raw),
        dedupe_key=raw["deduplication"]["dedupe_key"],
        reason_code=decision.reason_code,
        parser_confidence=confidence,
    )


def _parse_payload(text: str) -> tuple[dict[str, Any], str | None]:
    normalized_text = normalize_message_text(text)
    if not normalized_text:
        return {}, reason_codes.CONTEXT_ONLY
    if PROMPT_INJECTION_RE.search(normalized_text):
        return {}, reason_codes.PROMPT_INJECTION_ATTEMPT

    symbol = normalize_symbol(normalized_text)
    long_seen, short_seen = side_tokens(normalized_text)
    if long_seen and short_seen:
        return {}, reason_codes.AMBIGUOUS_DIRECTION
    side = normalize_side(normalized_text)

    entry = (
        extract_decimal_after(normalized_text, ENTRY_LABELS)
        or _entry_from_side_phrase(normalized_text)
        or extract_first_decimal(normalized_text)
    )
    stop = extract_decimal_after(normalized_text, STOP_LABELS)
    target = extract_decimal_after(normalized_text, TARGET_LABELS)
    quantity = extract_decimal_after(normalized_text, QUANTITY_LABELS)

    if symbol is None and any(token in normalized_text for token in ("long", "short", "entry", "stop", "target")):
        return {}, reason_codes.UNSUPPORTED_SYMBOL
    if symbol is None and side is None and entry is None:
        return {}, reason_codes.CONTEXT_ONLY

    payload = {
        "candidate_type": "trade_signal",
        "symbol": symbol,
        "subject": symbol,
        "side": side,
        "direction_or_outcome": side,
        "entry_price": decimal_to_json_number(entry),
        "quantity": decimal_to_json_number(quantity),
        "stop_loss": decimal_to_json_number(stop),
        "take_profit": decimal_to_json_number(target),
        "summary": "Sanitized v13-compatible trade signal.",
    }
    return {key: value for key, value in payload.items() if value is not None}, None


def _entry_from_side_phrase(text: str):
    match = re.search(
        r"\b(?:long|short|buy|sell)\b[^0-9]{0,18}(\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)([km]?)",
        text,
        re.I,
    )
    if not match:
        return None
    return decimal_from_token(match.group(1), match.group(2))


def _raw_source_event(envelope: Mapping[str, Any]) -> dict[str, Any]:
    raw = envelope.get("raw_source_event", envelope)
    if not isinstance(raw, Mapping):
        raise ValueError("raw_source_event must be an object")
    return json.loads(json.dumps(raw, sort_keys=True))


def _with_derived_dedupe(raw: dict[str, Any], text: str) -> dict[str, Any]:
    source_ref = raw.get("private_source_ref")
    if not isinstance(source_ref, Mapping):
        raise ValueError("raw_source_event.private_source_ref is required")
    source_id = str(source_ref.get("source_ref_id") or "")
    content_hash = content_hash_for_text(text)
    dedupe_key = dedupe_key_for(source_id=source_id, content_hash=content_hash)

    updated = dict(raw)
    content = dict(updated.get("content") or {})
    content["content_hash"] = content_hash
    content.setdefault("content_excerpt", "Sanitized parser compatibility fixture.")
    content.setdefault("content_mime", "text/plain")
    content.setdefault("sanitized", True)
    updated["content"] = content

    dedupe = dict(updated.get("deduplication") or {})
    dedupe["dedupe_key"] = dedupe_key
    dedupe.setdefault("duplicate", False)
    dedupe.setdefault("duplicate_of_raw_event_id", None)
    updated["deduplication"] = dedupe

    lineage = dict(updated.get("lineage") or {})
    lineage["raw_payload_hash"] = content_hash
    updated["lineage"] = lineage
    return updated


def _parse_attempt(
    *,
    raw: Mapping[str, Any],
    normalized_payload: Mapping[str, Any],
    decision: Any,
    confidence: int,
    mode: str,
    created_at: str,
) -> dict[str, Any]:
    parse_attempt_id = _stable_id(
        "parse",
        raw["raw_event_id"],
        raw["content"]["content_hash"],
        PARSER_VERSION,
    )
    accepted = bool(decision.accepted)
    return {
        "schema_version": "internal.parse_attempt.v1",
        "parse_attempt_id": parse_attempt_id,
        "raw_event_id": raw["raw_event_id"],
        "parser": {
            "name": PARSER_NAME,
            "version": PARSER_VERSION,
            "mode": mode,
        },
        "created_at": created_at,
        "accepted": accepted,
        "status": "accepted" if accepted else "rejected",
        "reason_codes": [decision.reason_code],
        "normalized_payload": dict(normalized_payload),
        "rejection_reason": None if accepted else decision.reason_code,
        "error_class": None if accepted else decision.diagnostic_category,
        "diagnostics": {
            "confidence": confidence,
            "field_warnings": list(decision.field_warnings),
            "provider_metadata": {
                "provider": "rule_based",
                "model": "none",
                "prompt_version": PARSER_VERSION,
            },
        },
        "lineage": {
            "raw_event_id": raw["raw_event_id"],
            "content_hash": raw["content"]["content_hash"],
        },
    }


def _accepted_candidate(
    raw: Mapping[str, Any],
    parse_attempt: Mapping[str, Any],
    confidence: int,
    created_at: str,
) -> dict[str, Any]:
    payload = dict(parse_attempt["normalized_payload"])
    candidate_id = _stable_id(
        "candidate",
        raw["raw_event_id"],
        parse_attempt["parse_attempt_id"],
        _canonical_json(payload),
    )
    evidence_hash = _evidence_hash(raw, parse_attempt, payload, confidence)
    source_ref = raw["private_source_ref"]
    return {
        "schema_version": "internal.accepted_candidate.v1",
        "accepted_candidate_id": candidate_id,
        "raw_event_id": raw["raw_event_id"],
        "parse_attempt_id": parse_attempt["parse_attempt_id"],
        "source_ref": {
            "source_ref_id": source_ref["source_ref_id"],
            "source_ref_type": source_ref["source_ref_type"],
            "privacy_classification": source_ref["privacy_classification"],
        },
        "parser_version": PARSER_VERSION,
        "candidate_type": str(payload["candidate_type"]),
        "normalized_payload": payload,
        "confidence": confidence / 100,
        "admission_policy_version": ADMISSION_POLICY_VERSION,
        "admission_reason": reason_codes.ACCEPTED_TRADE_SIGNAL,
        "evidence_hash": evidence_hash,
        "status": "accepted",
        "created_at": created_at,
        "lineage": {
            "raw_event_id": raw["raw_event_id"],
            "parse_attempt_id": parse_attempt["parse_attempt_id"],
            "content_hash": raw["content"]["content_hash"],
        },
    }


def _parser_rejection(
    raw: Mapping[str, Any],
    parse_attempt: Mapping[str, Any],
    decision: Any,
    created_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": "internal.parser_rejection.v1",
        "parser_rejection_id": _stable_id(
            "parser_rejection",
            raw["raw_event_id"],
            parse_attempt["parse_attempt_id"],
            decision.reason_code,
        ),
        "raw_event_id": raw["raw_event_id"],
        "parse_attempt_id": parse_attempt["parse_attempt_id"],
        "reason_code": decision.reason_code,
        "diagnostic_category": decision.diagnostic_category,
        "retryable": bool(decision.retryable),
        "parser": {
            "name": PARSER_NAME,
            "version": PARSER_VERSION,
            "mode": parse_attempt["parser"]["mode"],
        },
        "created_at": created_at,
        "safe_diagnostic": reason_codes.safe_diagnostic(decision.reason_code),
        "lineage": {
            "raw_event_id": raw["raw_event_id"],
            "parse_attempt_id": parse_attempt["parse_attempt_id"],
            "content_hash": raw["content"]["content_hash"],
        },
    }


def _parser_confidence(payload: Mapping[str, Any], accepted: bool) -> int:
    if not accepted:
        return 0
    score = 63
    for field in ("symbol", "side", "entry_price", "stop_loss", "take_profit"):
        if payload.get(field) is not None:
            score += 4
    if payload.get("quantity") is not None:
        score += 3
    return min(score, 90)


def _private_lineage(envelope: Mapping[str, Any], raw: Mapping[str, Any]) -> dict[str, Any]:
    fixture_lineage = envelope.get("private_lineage")
    return {
        "raw_event_id": raw["raw_event_id"],
        "private_source_ref": dict(raw["private_source_ref"]),
        "dedupe_key": raw["deduplication"]["dedupe_key"],
        "message_lineage": dict(fixture_lineage) if isinstance(fixture_lineage, Mapping) else {},
        "source_filter_semantics": "watched_channels_and_parent_threads",
    }


def _evidence_hash(
    raw: Mapping[str, Any],
    parse_attempt: Mapping[str, Any],
    payload: Mapping[str, Any],
    confidence: int,
) -> str:
    return "sha256:" + hashlib.sha256(
        (
            "foxclaw.parser_v13.accepted_candidate\n"
            + raw["raw_event_id"]
            + "\n"
            + parse_attempt["parse_attempt_id"]
            + "\n"
            + _canonical_json(payload)
            + "\n"
            + str(confidence)
            + "\n"
            + PARSER_VERSION
        ).encode("utf-8")
    ).hexdigest()


def _stable_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha256(
        ("foxclaw.parser_v13." + prefix + "\n" + "\n".join(map(str, parts))).encode("utf-8")
    ).hexdigest()
    return f"{prefix}_{digest[:24]}"


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _schema(name: str) -> dict[str, Any]:
    return json.loads(Path(schema_path(name)).read_text(encoding="utf-8"))
