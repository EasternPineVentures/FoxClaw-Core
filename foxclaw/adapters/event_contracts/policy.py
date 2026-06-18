"""Event-contract-specific policy verdicts."""

from __future__ import annotations

from .contracts import EventContractPolicyVerdict, EvidenceDossier, ResolutionQualityVerdict


def assess_event_contract_policy(
    *,
    market_id: str,
    dossier: EvidenceDossier,
    resolution_quality: ResolutionQualityVerdict,
) -> EventContractPolicyVerdict:
    reasons: list[str] = []
    if not dossier.evidence:
        reasons.append("no_allowed_public_evidence")
    if dossier.rejected_evidence:
        reasons.append("some_evidence_rejected")
    if resolution_quality.blocks_paper_entry:
        reasons.extend(resolution_quality.reasons)
    can_enter_paper = not reasons
    return EventContractPolicyVerdict(
        market_id=market_id,
        can_enter_paper=can_enter_paper,
        can_publish=bool(dossier.evidence) and not dossier.can_execute_trades,
        can_submit_order=False,
        can_move_funds=False,
        live_execution_allowed=False,
        authority_level="A4_prohibited",
        reasons=tuple(reasons) if reasons else ("paper_entry_allowed",),
    )
