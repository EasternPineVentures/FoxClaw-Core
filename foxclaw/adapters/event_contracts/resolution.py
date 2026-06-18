"""Resolution-quality checks and settlement receipts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping

from .contracts import ResolutionQualityVerdict, ResolutionReceipt, utc_now


def assess_resolution_quality(market: Mapping[str, Any] | Any) -> ResolutionQualityVerdict:
    market_id = _field(market, "market_id", "ticker")
    rule_text = _optional_field(market, "resolution_rule_text", "rules_primary", "resolution_rule")
    settlement_sources = _tuple_field(market, "settlement_sources")
    reasons: list[str] = []
    score = Decimal("0")
    if rule_text:
        score += Decimal("0.50")
    else:
        reasons.append("missing_resolution_rule")
    if settlement_sources:
        score += Decimal("0.50")
    else:
        reasons.append("missing_settlement_source")
    blocks = bool(reasons)
    return ResolutionQualityVerdict(
        market_id=market_id,
        has_rule_text=bool(rule_text),
        has_settlement_source=bool(settlement_sources),
        clarity_score=score,
        blocks_paper_entry=blocks,
        reasons=tuple(reasons) if reasons else ("clear_resolution_rule",),
    )


def record_resolution(
    market: Mapping[str, Any] | Any,
    outcome: str,
    evidence_url: str,
    *,
    resolved_at: datetime | None = None,
    settlement_note: str | None = None,
) -> ResolutionReceipt:
    market_id = _field(market, "market_id", "ticker")
    note = settlement_note or f"{market_id} resolved {outcome}"
    return ResolutionReceipt(
        market_id=market_id,
        resolved_outcome=str(outcome).strip().lower(),
        resolved_at=resolved_at or utc_now(),
        evidence_url=str(evidence_url).strip(),
        settlement_note=note,
        public_information_only=True,
    )


def _field(market: Mapping[str, Any] | Any, *names: str) -> str:
    value = _optional_field(market, *names)
    if not value:
        raise ValueError(f"market missing required field from {names}")
    return value


def _optional_field(market: Mapping[str, Any] | Any, *names: str) -> str | None:
    for name in names:
        value = market.get(name) if isinstance(market, Mapping) else getattr(market, name, None)
        text = str(value or "").strip()
        if text:
            return text
    return None


def _tuple_field(market: Mapping[str, Any] | Any, name: str) -> tuple[str, ...]:
    value = market.get(name) if isinstance(market, Mapping) else getattr(market, name, ())
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    return tuple(str(item).strip() for item in value if str(item).strip())
