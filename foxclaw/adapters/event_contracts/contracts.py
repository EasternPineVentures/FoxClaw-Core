"""Forecast Desk evidence, resolution, and policy contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class EvidenceEligibilityVerdict:
    source_id: str
    allowed: bool
    source_classification: str
    reason: str
    public_information_only: bool

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.reason:
            raise ValueError("reason is required")


@dataclass(frozen=True)
class EvidenceItem:
    source_id: str
    title: str
    url: str
    source_type: str
    claims: tuple[str, ...]
    independence_group: str
    eligibility: EvidenceEligibilityVerdict
    raw_payload_hash: str

    def __post_init__(self) -> None:
        if not self.eligibility.allowed:
            raise ValueError("EvidenceItem may only wrap allowed evidence")
        if not self.url.startswith(("https://", "http://")):
            raise ValueError("evidence url must be public HTTP(S)")
        if not self.independence_group:
            raise ValueError("independence_group is required")
        if not self.raw_payload_hash.startswith("sha256:"):
            raise ValueError("raw_payload_hash must be sha256-prefixed")


@dataclass(frozen=True)
class EvidenceDossier:
    market_id: str
    title: str
    resolution_rule_text: str | None
    settlement_sources: tuple[str, ...]
    evidence: tuple[EvidenceItem, ...]
    rejected_evidence: tuple[EvidenceEligibilityVerdict, ...]
    duplicate_evidence_collapsed: int
    independence_group_count: int
    contradiction_count: int
    evidence_quality: Decimal
    dossier_hash: str
    can_authorize_execution: bool = False
    can_execute_trades: bool = False
    can_mutate_grove: bool = False

    def __post_init__(self) -> None:
        if not self.market_id:
            raise ValueError("market_id is required")
        if not self.dossier_hash.startswith("sha256:"):
            raise ValueError("dossier_hash must be sha256-prefixed")
        if not Decimal("0") <= self.evidence_quality <= Decimal("1"):
            raise ValueError("evidence_quality must be in [0, 1]")
        if self.can_authorize_execution or self.can_execute_trades or self.can_mutate_grove:
            raise ValueError("dossiers are advisory receipts and cannot authorize action")


@dataclass(frozen=True)
class ResolutionQualityVerdict:
    market_id: str
    has_rule_text: bool
    has_settlement_source: bool
    clarity_score: Decimal
    blocks_paper_entry: bool
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if not Decimal("0") <= self.clarity_score <= Decimal("1"):
            raise ValueError("clarity_score must be in [0, 1]")
        if self.blocks_paper_entry and not self.reasons:
            raise ValueError("blocking verdicts must explain why")


@dataclass(frozen=True)
class ResolutionReceipt:
    market_id: str
    resolved_outcome: str
    resolved_at: datetime
    evidence_url: str
    settlement_note: str
    public_information_only: bool
    can_move_funds: bool = False
    can_submit_order: bool = False

    def __post_init__(self) -> None:
        if self.resolved_outcome not in {"yes", "no", "void"}:
            raise ValueError("resolved_outcome must be yes, no, or void")
        if self.resolved_at.tzinfo is None or self.resolved_at.utcoffset() is None:
            raise ValueError("resolved_at must be timezone-aware")
        if not self.evidence_url.startswith(("https://", "http://")):
            raise ValueError("resolution evidence_url must be public HTTP(S)")
        if not self.public_information_only:
            raise ValueError("resolution receipts require public information")
        if self.can_move_funds or self.can_submit_order:
            raise ValueError("resolution receipts cannot move funds or submit orders")


@dataclass(frozen=True)
class EventContractPolicyVerdict:
    market_id: str
    can_enter_paper: bool
    can_publish: bool
    can_submit_order: bool
    can_move_funds: bool
    live_execution_allowed: bool
    authority_level: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ForecastReceipt:
    market_id: str
    side: str
    verdict: str
    independent_probability: Decimal
    market_probability: Decimal | None
    costs_total: Decimal
    usable_edge: Decimal
    minimum_usable_edge: Decimal
    evidence_quality: Decimal
    dossier_hash: str
    engine_subject: str
    engine_tier: str
    gate_multiplier: Decimal
    raw_commitment: Decimal
    adjusted_commitment: Decimal
    reason: str
    code_version: str
    created_at: datetime
    mode: str = "PAPER"
    can_submit_order: bool = False
    can_move_funds: bool = False
    live_execution_allowed: bool = False

    def __post_init__(self) -> None:
        if self.side not in {"yes", "no", "none"}:
            raise ValueError("side must be yes, no, or none")
        if self.verdict not in {"reject", "watch", "paper"}:
            raise ValueError("verdict must be reject, watch, or paper")
        for label in (
            "independent_probability",
            "costs_total",
            "usable_edge",
            "minimum_usable_edge",
            "evidence_quality",
            "gate_multiplier",
            "raw_commitment",
            "adjusted_commitment",
        ):
            value = getattr(self, label)
            if not isinstance(value, Decimal) or not value.is_finite():
                raise TypeError(f"{label} must be finite Decimal")
        if self.market_probability is not None and (
            not isinstance(self.market_probability, Decimal) or not self.market_probability.is_finite()
        ):
            raise TypeError("market_probability must be finite Decimal or None")
        if self.can_submit_order or self.can_move_funds or self.live_execution_allowed:
            raise ValueError("forecast receipts are paper-only and cannot authorize live action")
        if self.mode != "PAPER":
            raise ValueError("forecast receipts are PAPER mode in this authority phase")


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)
