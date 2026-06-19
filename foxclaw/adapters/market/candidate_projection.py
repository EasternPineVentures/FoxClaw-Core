"""Conservative accepted-candidate projection for the private Microscope."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping

PROJECTION_VERSION = "market_candidate_projection.v1"

TEXT_FIELDS = (
    "candidate_type",
    "subject",
    "symbol",
    "direction_or_outcome",
    "side",
    "summary",
    "time_horizon",
)
NUMBER_FIELDS = ("entry_price", "stop_loss", "take_profit")
PROJECTED_FIELDS = (*TEXT_FIELDS, *NUMBER_FIELDS)


class CandidateProjectionError(ValueError):
    """Base error for candidate projection failures."""


class CandidatePayloadDecodeError(CandidateProjectionError):
    """Raised when normalized_payload_json is malformed JSON."""


class CandidatePayloadTypeError(CandidateProjectionError):
    """Raised when normalized_payload_json is valid JSON but not an object."""


@dataclass(frozen=True)
class CandidateProjection:
    projection_version: str
    candidate_type: str | None
    subject: str | None
    symbol: str | None
    direction_or_outcome: str | None
    side: str | None
    summary: str | None
    time_horizon: str | None
    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None
    parser_confidence: float | None
    public_fields: dict[str, Any]
    internal_lineage: dict[str, Any]
    missing_fields: tuple[str, ...]
    payload: dict[str, Any]


def decode_candidate_payload(raw_json: str) -> dict[str, Any]:
    """Strictly decode normalized_payload_json into an object."""
    try:
        decoded = json.loads(str(raw_json))
    except json.JSONDecodeError as exc:
        raise CandidatePayloadDecodeError("normalized_payload_json is malformed") from exc
    if not isinstance(decoded, dict):
        raise CandidatePayloadTypeError("normalized_payload_json must decode to an object")
    return decoded


def project_candidate(candidate: Mapping[str, Any]) -> CandidateProjection:
    """Project only explicit payload fields; never infer from summary text."""
    payload = decode_candidate_payload(str(candidate.get("normalized_payload_json") or ""))
    values: dict[str, Any] = {}
    for field in TEXT_FIELDS:
        values[field] = _text_value(payload, field)
    for field in NUMBER_FIELDS:
        values[field] = _number_value(payload, field)

    public_fields = {
        field: values[field]
        for field in PROJECTED_FIELDS
        if values[field] is not None
    }
    internal_lineage = {
        "candidate_id": candidate.get("candidate_id"),
        "candidate_uid": candidate.get("candidate_uid"),
        "receipt_id": candidate.get("receipt_id"),
        "event_id": candidate.get("event_id"),
        "attempt_id": candidate.get("attempt_id"),
        "source_id": candidate.get("source_id"),
        "source_type": candidate.get("source_type"),
        "parser_version": candidate.get("parser_version"),
        "evidence_hash": candidate.get("evidence_hash"),
        "created_at": candidate.get("created_at"),
    }
    missing = tuple(field for field in PROJECTED_FIELDS if values[field] is None)
    confidence = candidate.get("confidence")
    return CandidateProjection(
        projection_version=PROJECTION_VERSION,
        candidate_type=values["candidate_type"],
        subject=values["subject"],
        symbol=values["symbol"],
        direction_or_outcome=values["direction_or_outcome"],
        side=values["side"],
        summary=values["summary"],
        time_horizon=values["time_horizon"],
        entry_price=values["entry_price"],
        stop_loss=values["stop_loss"],
        take_profit=values["take_profit"],
        parser_confidence=None if confidence is None else float(confidence),
        public_fields=public_fields,
        internal_lineage=internal_lineage,
        missing_fields=missing,
        payload=dict(payload),
    )


def projection_to_dict(projection: CandidateProjection) -> dict[str, Any]:
    """Return a JSON-ready projection dictionary."""
    return {
        "projection_version": projection.projection_version,
        "candidate_type": projection.candidate_type,
        "subject": projection.subject,
        "symbol": projection.symbol,
        "direction_or_outcome": projection.direction_or_outcome,
        "side": projection.side,
        "summary": projection.summary,
        "time_horizon": projection.time_horizon,
        "entry_price": projection.entry_price,
        "stop_loss": projection.stop_loss,
        "take_profit": projection.take_profit,
        "missing_fields": list(projection.missing_fields),
        "public_fields": dict(projection.public_fields),
    }


def _text_value(payload: Mapping[str, Any], field: str) -> str | None:
    if field not in payload or payload[field] is None:
        return None
    value = payload[field]
    if not isinstance(value, str):
        raise CandidateProjectionError(f"{field} must be a string when present")
    return value


def _number_value(payload: Mapping[str, Any], field: str) -> float | None:
    if field not in payload or payload[field] is None:
        return None
    value = payload[field]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise CandidateProjectionError(f"{field} must be numeric when present")
    return float(value)
