"""Public-evidence dossiers for event-contract markets."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from foxclaw.adapters.event_contracts.markets import to_jsonable

from .contracts import EvidenceDossier, EvidenceEligibilityVerdict, EvidenceItem
from .kalshi.models import payload_hash

_BANNED_CLASSIFICATIONS = {
    "access_control_bypass",
    "classified",
    "contractor_private",
    "doxxed",
    "employer_private",
    "hacked",
    "insider",
    "leaked_private",
    "material_nonpublic",
    "mnpi",
    "nonpublic",
    "paywall_bypass",
    "private_communication",
    "restricted",
    "stolen",
}


def assess_evidence_eligibility(raw: Mapping[str, Any]) -> EvidenceEligibilityVerdict:
    source_id = _text(raw.get("source_id") or raw.get("url") or raw.get("title") or "evidence")
    classification = _text(raw.get("source_classification") or raw.get("classification") or "public")
    public_flag = bool(raw.get("public", True))
    if not public_flag:
        return EvidenceEligibilityVerdict(
            source_id=source_id,
            allowed=False,
            source_classification=classification,
            reason="source explicitly marked nonpublic",
            public_information_only=False,
        )
    if classification.lower() in _BANNED_CLASSIFICATIONS:
        return EvidenceEligibilityVerdict(
            source_id=source_id,
            allowed=False,
            source_classification=classification,
            reason=f"source classification rejected: {classification}",
            public_information_only=False,
        )
    url = _text(raw.get("url"))
    if not url.startswith(("https://", "http://")):
        return EvidenceEligibilityVerdict(
            source_id=source_id,
            allowed=False,
            source_classification=classification,
            reason="missing public HTTP(S) URL",
            public_information_only=False,
        )
    return EvidenceEligibilityVerdict(
        source_id=source_id,
        allowed=True,
        source_classification=classification,
        reason="lawfully public source accepted",
        public_information_only=True,
    )


def build_dossier(market: Mapping[str, Any] | Any, evidence: list[Mapping[str, Any]]) -> EvidenceDossier:
    """Assemble a market's public-evidence dossier with duplicate-source collapse."""

    market_id = _market_field(market, "market_id", "ticker")
    title = _market_field(market, "title") or market_id
    resolution_rule_text = _optional_market_field(
        market,
        "resolution_rule_text",
        "rules_primary",
        "resolution_rule",
        "market_rules",
    )
    settlement_sources = _tuple_field(market, "settlement_sources")
    accepted: list[EvidenceItem] = []
    rejected: list[EvidenceEligibilityVerdict] = []
    groups_seen: set[str] = set()
    duplicates = 0
    contradictions = 0

    for raw in evidence:
        verdict = assess_evidence_eligibility(raw)
        if not verdict.allowed:
            rejected.append(verdict)
            continue
        group = _text(raw.get("independence_group") or raw.get("source_id") or raw.get("url"))
        if group in groups_seen:
            duplicates += 1
            continue
        groups_seen.add(group)
        if bool(raw.get("contradicts", False)):
            contradictions += 1
        accepted.append(
            EvidenceItem(
                source_id=verdict.source_id,
                title=_text(raw.get("title") or verdict.source_id),
                url=_text(raw.get("url")),
                source_type=_text(raw.get("source_type") or "public"),
                claims=tuple(_text(claim) for claim in raw.get("claims", ()) if _text(claim)),
                independence_group=group,
                eligibility=verdict,
                raw_payload_hash=payload_hash(raw),
            )
        )

    quality = _quality(
        evidence_groups=len(groups_seen),
        has_rule=bool(resolution_rule_text),
        has_settlement_source=bool(settlement_sources),
        contradictions=contradictions,
    )
    hash_payload = {
        "market_id": market_id,
        "resolution_rule_text": resolution_rule_text,
        "settlement_sources": settlement_sources,
        "evidence": [to_jsonable(item) for item in accepted],
        "rejected": [to_jsonable(item) for item in rejected],
        "duplicates": duplicates,
        "contradictions": contradictions,
        "quality": format(quality, "f"),
    }
    return EvidenceDossier(
        market_id=market_id,
        title=title,
        resolution_rule_text=resolution_rule_text,
        settlement_sources=settlement_sources,
        evidence=tuple(accepted),
        rejected_evidence=tuple(rejected),
        duplicate_evidence_collapsed=duplicates,
        independence_group_count=len(groups_seen),
        contradiction_count=contradictions,
        evidence_quality=quality,
        dossier_hash=payload_hash(hash_payload),
    )


def _quality(*, evidence_groups: int, has_rule: bool, has_settlement_source: bool,
             contradictions: int) -> Decimal:
    score = Decimal("0")
    if has_rule:
        score += Decimal("0.25")
    if has_settlement_source:
        score += Decimal("0.25")
    score += min(Decimal("0.50"), Decimal(evidence_groups) * Decimal("0.20"))
    score -= min(Decimal("0.25"), Decimal(contradictions) * Decimal("0.10"))
    return max(Decimal("0"), min(Decimal("1"), score))


def _market_field(market: Mapping[str, Any] | Any, *names: str) -> str:
    value = _optional_market_field(market, *names)
    if not value:
        raise ValueError(f"market missing required field from {names}")
    return value


def _optional_market_field(market: Mapping[str, Any] | Any, *names: str) -> str | None:
    for name in names:
        value = market.get(name) if isinstance(market, Mapping) else getattr(market, name, None)
        text = _text(value)
        if text:
            return text
    return None


def _tuple_field(market: Mapping[str, Any] | Any, name: str) -> tuple[str, ...]:
    value = market.get(name) if isinstance(market, Mapping) else getattr(market, name, ())
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    return tuple(_text(item) for item in value if _text(item))


def _text(value: Any) -> str:
    return str(value or "").strip()
