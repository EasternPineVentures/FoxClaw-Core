"""Policy checks for presenting readiness verdicts publicly."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .risk_classification import RISK_REDLINE, RISK_REJECT, normalize_risk_class


@dataclass(frozen=True)
class ReadinessPolicyResult:
    allowed: bool
    reason_codes: tuple[str, ...]
    authority: str = "paper_readiness_only"


def evaluate_public_trade_idea_readiness(verdict: Mapping[str, Any] | None) -> ReadinessPolicyResult:
    """Require a readiness verdict before a public item can be framed as a trade idea."""
    if not verdict:
        return ReadinessPolicyResult(False, ("missing_readiness_verdict",))
    reasons: list[str] = []
    risk_class = normalize_risk_class(str(verdict.get("risk_class", "")))
    plan_readiness = str(verdict.get("plan_readiness", "")).strip().upper()
    can_present = bool(verdict.get("can_present_as_trade_idea"))
    if risk_class in {RISK_REDLINE, RISK_REJECT}:
        reasons.append("risk_class_blocks_trade_idea")
    if plan_readiness != "PAPER_READY":
        reasons.append("plan_not_paper_ready")
    if not can_present:
        reasons.append("readiness_verdict_does_not_allow_trade_idea")
    return ReadinessPolicyResult(
        allowed=not reasons,
        reason_codes=tuple(dict.fromkeys(reasons)) or ("public_trade_idea_readiness_passed",),
    )
