"""Trusted evidence intake for Forecast Desk dossiers.

Trusted submitters may add context. They cannot set probabilities, publish forecasts,
enter paper positions, submit orders, or move funds.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from .dossiers import assess_evidence_eligibility
from .kalshi.models import payload_hash

SUBMIT_EVIDENCE_CAPABILITY = "submit_evidence"
CONTEXT_ONLY_AUTHORITY = "context_only"

PROHIBITED_INTAKE_FIELDS = frozenset(
    {
        "adjusted_commitment",
        "authority_level",
        "can_enter_paper",
        "can_move_funds",
        "can_publish",
        "can_set_probability",
        "can_submit_order",
        "confidence",
        "independent_probability",
        "live_execution_allowed",
        "market_probability",
        "paper_size",
        "probability",
        "raw_commitment",
        "side",
        "trade",
        "verdict",
    }
)

_VALIDATION_STATUSES = frozenset({"accepted", "rejected", "duplicate"})


@dataclass(frozen=True)
class TrustedSubmitter:
    submitter_id: str
    display_name: str
    trust_tier: str
    capabilities: tuple[str, ...]
    active: bool = True
    can_set_probability: bool = False
    can_publish: bool = False
    can_enter_paper: bool = False
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False

    def __post_init__(self) -> None:
        if not _text(self.submitter_id):
            raise ValueError("submitter_id is required")
        if not _text(self.display_name):
            raise ValueError("display_name is required")
        if not _text(self.trust_tier):
            raise ValueError("trust_tier is required")
        if not isinstance(self.capabilities, tuple):
            raise TypeError("capabilities must be a tuple")
        if any(
            (
                self.can_set_probability,
                self.can_publish,
                self.can_enter_paper,
                self.can_submit_order,
                self.can_move_funds,
                self.live_execution_allowed,
            )
        ):
            raise ValueError("trusted submitters cannot carry execution or publication authority")

    @property
    def can_submit_evidence(self) -> bool:
        return self.active and SUBMIT_EVIDENCE_CAPABILITY in self.capabilities


@dataclass(frozen=True)
class EvidencePacket:
    packet_id: str
    submitter_id: str
    trust_tier: str
    market_id: str
    source_id: str
    title: str
    url: str
    source_type: str
    source_classification: str
    claims: tuple[str, ...]
    independence_group: str
    public_information_only_claimed: bool
    submitted_at: datetime
    raw_payload_hash: str
    status: str = "pending_review"
    authority_level: str = CONTEXT_ONLY_AUTHORITY
    can_set_probability: bool = False
    can_publish: bool = False
    can_enter_paper: bool = False
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False

    def __post_init__(self) -> None:
        for label in (
            "packet_id",
            "submitter_id",
            "trust_tier",
            "market_id",
            "source_id",
            "title",
            "url",
            "source_type",
            "source_classification",
            "independence_group",
            "raw_payload_hash",
        ):
            if not _text(getattr(self, label)):
                raise ValueError(f"{label} is required")
        if not self.packet_id.startswith("sha256:"):
            raise ValueError("packet_id must be sha256-prefixed")
        if not self.raw_payload_hash.startswith("sha256:"):
            raise ValueError("raw_payload_hash must be sha256-prefixed")
        if not self.url.startswith(("https://", "http://")):
            raise ValueError("evidence url must be public HTTP(S)")
        if not self.claims:
            raise ValueError("at least one claim is required")
        if self.submitted_at.tzinfo is None or self.submitted_at.utcoffset() is None:
            raise ValueError("submitted_at must be timezone-aware")
        if self.authority_level != CONTEXT_ONLY_AUTHORITY:
            raise ValueError("evidence packets are context-only")
        if any(
            (
                self.can_set_probability,
                self.can_publish,
                self.can_enter_paper,
                self.can_submit_order,
                self.can_move_funds,
                self.live_execution_allowed,
            )
        ):
            raise ValueError("evidence packets cannot carry authority")


@dataclass(frozen=True)
class IntakeValidation:
    validation_id: str
    packet_id: str
    market_id: str
    source_id: str
    accepted_for_dossier: bool
    status: str
    reasons: tuple[str, ...]
    public_information_only: bool
    duplicate_key: str
    validated_at: datetime
    can_authorize_execution: bool = False
    can_publish: bool = False
    can_enter_paper: bool = False
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False

    def __post_init__(self) -> None:
        for label in ("validation_id", "packet_id", "market_id", "source_id", "duplicate_key"):
            if not _text(getattr(self, label)):
                raise ValueError(f"{label} is required")
        if not self.validation_id.startswith("sha256:"):
            raise ValueError("validation_id must be sha256-prefixed")
        if self.status not in _VALIDATION_STATUSES:
            raise ValueError(f"unsupported validation status: {self.status}")
        if not self.reasons:
            raise ValueError("validation reasons are required")
        if self.accepted_for_dossier and (
            self.status != "accepted" or not self.public_information_only
        ):
            raise ValueError("accepted intake must be public and accepted")
        if self.validated_at.tzinfo is None or self.validated_at.utcoffset() is None:
            raise ValueError("validated_at must be timezone-aware")
        if any(
            (
                self.can_authorize_execution,
                self.can_publish,
                self.can_enter_paper,
                self.can_submit_order,
                self.can_move_funds,
                self.live_execution_allowed,
            )
        ):
            raise ValueError("intake validation cannot authorize action")


def submit_evidence_packet(
    submitter: TrustedSubmitter,
    raw: Mapping[str, Any],
    *,
    submitted_at: datetime | None = None,
) -> EvidencePacket:
    """Normalize one trusted evidence submission into a context-only packet."""

    if not submitter.can_submit_evidence:
        raise PermissionError(f"submitter {submitter.submitter_id!r} cannot submit evidence")
    if not isinstance(raw, Mapping):
        raise TypeError("raw evidence submission must be a mapping")
    _reject_authority_fields(raw)
    observed = _utc(submitted_at)
    normalized = _normalize_raw_submission(raw)
    raw_hash = payload_hash(normalized)
    packet_id = payload_hash(
        {
            "kind": "trusted_evidence_packet",
            "submitter_id": submitter.submitter_id,
            "market_id": normalized["market_id"],
            "raw_payload_hash": raw_hash,
        }
    )
    return EvidencePacket(
        packet_id=packet_id,
        submitter_id=submitter.submitter_id,
        trust_tier=submitter.trust_tier,
        market_id=normalized["market_id"],
        source_id=normalized["source_id"],
        title=normalized["title"],
        url=normalized["url"],
        source_type=normalized["source_type"],
        source_classification=normalized["source_classification"],
        claims=tuple(normalized["claims"]),
        independence_group=normalized["independence_group"],
        public_information_only_claimed=bool(normalized["public"]),
        submitted_at=observed,
        raw_payload_hash=raw_hash,
    )


def validate_evidence_packet(
    packet: EvidencePacket,
    *,
    seen_duplicate_keys: tuple[str, ...] = (),
    validated_at: datetime | None = None,
) -> IntakeValidation:
    """Apply dossier eligibility and duplicate checks to a trusted intake packet."""

    dossier_evidence = packet_to_dossier_evidence(packet)
    verdict = assess_evidence_eligibility(dossier_evidence)
    duplicate_key = packet.independence_group
    is_duplicate = duplicate_key in set(seen_duplicate_keys)
    if is_duplicate:
        status = "duplicate"
        accepted = False
        reasons = ("duplicate_independence_group",)
        public_only = verdict.public_information_only
    elif verdict.allowed:
        status = "accepted"
        accepted = True
        reasons = (verdict.reason,)
        public_only = True
    else:
        status = "rejected"
        accepted = False
        reasons = (verdict.reason,)
        public_only = verdict.public_information_only

    payload = {
        "packet_id": packet.packet_id,
        "market_id": packet.market_id,
        "source_id": packet.source_id,
        "status": status,
        "accepted_for_dossier": accepted,
        "reasons": reasons,
        "duplicate_key": duplicate_key,
    }
    return IntakeValidation(
        validation_id=payload_hash(payload),
        packet_id=packet.packet_id,
        market_id=packet.market_id,
        source_id=packet.source_id,
        accepted_for_dossier=accepted,
        status=status,
        reasons=reasons,
        public_information_only=public_only,
        duplicate_key=duplicate_key,
        validated_at=_utc(validated_at),
    )


def packet_to_dossier_evidence(packet: EvidencePacket) -> dict[str, Any]:
    return {
        "source_id": packet.source_id,
        "title": packet.title,
        "url": packet.url,
        "source_type": packet.source_type,
        "source_classification": packet.source_classification,
        "public": packet.public_information_only_claimed,
        "claims": list(packet.claims),
        "independence_group": packet.independence_group,
        "trusted_intake_packet_id": packet.packet_id,
        "trusted_submitter_id": packet.submitter_id,
        "trusted_submitter_tier": packet.trust_tier,
        "raw_payload_hash": packet.raw_payload_hash,
    }


def _normalize_raw_submission(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise TypeError("raw evidence submission must be a mapping")
    url = _required_text(raw.get("url"), "url")
    source_id = _text(raw.get("source_id")) or url
    title = _text(raw.get("title")) or source_id
    claims = _claims(raw.get("claims", ()))
    independence_group = _text(raw.get("independence_group")) or source_id
    return {
        "market_id": _required_text(raw.get("market_id"), "market_id"),
        "source_id": source_id,
        "title": title,
        "url": url,
        "source_type": _text(raw.get("source_type")) or "public",
        "source_classification": _text(raw.get("source_classification")) or "public",
        "claims": list(claims),
        "independence_group": independence_group,
        "public": bool(raw.get("public", True)),
    }


def _reject_authority_fields(raw: Mapping[str, Any]) -> None:
    present = sorted(key for key in PROHIBITED_INTAKE_FIELDS if key in raw)
    if present:
        raise ValueError(f"trusted evidence cannot include authority fields: {', '.join(present)}")


def _claims(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        out = (_text(value),)
    elif value is None:
        out = ()
    else:
        out = tuple(_text(item) for item in value)
    clean = tuple(item for item in out if item)
    if not clean:
        raise ValueError("at least one claim is required")
    return clean


def _utc(value: datetime | None) -> datetime:
    return (value or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)


def _required_text(value: Any, label: str) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _text(value: Any) -> str:
    return str(value or "").strip()
