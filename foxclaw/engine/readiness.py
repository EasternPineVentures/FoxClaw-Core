"""Professional readiness verdicts.

A strong signal can still be a bad professional action. This module keeps the
readiness dimensions separate and produces an explainable verdict.
"""
from __future__ import annotations

from dataclasses import dataclass

RISK_RESEARCH = "RESEARCH"
RISK_WATCH = "WATCH"
RISK_STRUCTURED = "STRUCTURED"
RISK_TACTICAL = "TACTICAL"
RISK_SPECULATIVE = "SPECULATIVE"
RISK_REDLINE = "REDLINE"
RISK_REJECT = "REJECT"

PLAN_NOT_PLANNED = "NOT_PLANNED"
PLAN_DRAFT = "DRAFT"
PLAN_PAPER_READY = "PAPER_READY"

GOOD_SIGNAL_BAD_TRADE = "GOOD_SIGNAL_BAD_TRADE"
STRUCTURED_READY = "STRUCTURED_READY"
WATCH_FOR_STRUCTURE = "WATCH_FOR_STRUCTURE"
RESEARCH_ONLY = "RESEARCH_ONLY"
REJECTED = "REJECTED"


@dataclass(frozen=True)
class ReadinessInput:
    attention: int
    evidence_quality: int
    signal_confidence: int
    cost_adjusted_edge: int
    tradeability: int
    entry_quality: int
    risk: int
    plan_readiness: int
    source_track_record: int
    setup_track_record: int


@dataclass(frozen=True)
class TradeReadinessVerdict:
    scores: dict[str, int]
    risk_class: str
    plan_readiness: str
    verdict: str
    public_summary: str
    professional_wait_for: str
    can_present_as_trade_idea: bool
    reason_codes: tuple[str, ...]


def assess_trade_readiness(values: ReadinessInput) -> TradeReadinessVerdict:
    """Produce a readiness verdict while preserving every underlying dimension."""
    scores = {
        "attention": _score(values.attention),
        "evidence_quality": _score(values.evidence_quality),
        "signal_confidence": _score(values.signal_confidence),
        "cost_adjusted_edge": _signed_score(values.cost_adjusted_edge),
        "tradeability": _score(values.tradeability),
        "entry_quality": _score(values.entry_quality),
        "risk": _score(values.risk),
        "plan_readiness": _score(values.plan_readiness),
        "source_track_record": _score(values.source_track_record),
        "setup_track_record": _score(values.setup_track_record),
    }
    plan_state = _plan_state(scores["plan_readiness"])
    reasons = _reason_codes(scores, plan_state)

    if scores["evidence_quality"] < 25 or scores["signal_confidence"] < 25:
        return _verdict(
            scores,
            risk_class=RISK_REJECT,
            plan_state=plan_state,
            verdict=REJECTED,
            summary="The claim is not supported well enough for a public trade idea.",
            wait_for="Independent public evidence and a clearer thesis.",
            can_present=False,
            reasons=("insufficient_signal_or_evidence", *reasons),
        )

    if _good_signal_bad_trade(scores, plan_state):
        risk_class = RISK_REDLINE if scores["risk"] >= 85 else RISK_WATCH
        return _verdict(
            scores,
            risk_class=risk_class,
            plan_state=plan_state,
            verdict=GOOD_SIGNAL_BAD_TRADE,
            summary=(
                "The directional thesis may be credible, but the current action is not "
                "professionally structured."
            ),
            wait_for=_wait_for(scores, plan_state),
            can_present=False,
            reasons=("good_signal_bad_trade", *reasons),
        )

    if _structured(scores, plan_state):
        risk_class = RISK_TACTICAL if scores["attention"] >= 85 else RISK_STRUCTURED
        return _verdict(
            scores,
            risk_class=risk_class,
            plan_state=plan_state,
            verdict=STRUCTURED_READY,
            summary="The thesis, evidence, entry quality, and plan are structured enough for paper review.",
            wait_for="Maintain invalidation, sizing, and exit discipline before any paper rehearsal.",
            can_present=True,
            reasons=("structured_ready", *reasons),
        )

    if scores["risk"] >= 75 or scores["cost_adjusted_edge"] < 0:
        risk_class = RISK_SPECULATIVE
    elif scores["evidence_quality"] < 55 or scores["signal_confidence"] < 55:
        risk_class = RISK_RESEARCH
    else:
        risk_class = RISK_WATCH
    return _verdict(
        scores,
        risk_class=risk_class,
        plan_state=plan_state,
        verdict=WATCH_FOR_STRUCTURE if risk_class != RISK_RESEARCH else RESEARCH_ONLY,
        summary="More structure is needed before this can be framed as a professional trade idea.",
        wait_for=_wait_for(scores, plan_state),
        can_present=False,
        reasons=tuple(reasons) or ("watch_for_structure",),
    )


def _good_signal_bad_trade(scores: dict[str, int], plan_state: str) -> bool:
    return (
        scores["signal_confidence"] >= 70
        and scores["evidence_quality"] >= 65
        and (
            scores["tradeability"] < 45
            or scores["entry_quality"] < 45
            or scores["risk"] >= 80
            or plan_state != PLAN_PAPER_READY
        )
    )


def _structured(scores: dict[str, int], plan_state: str) -> bool:
    return (
        scores["evidence_quality"] >= 65
        and scores["signal_confidence"] >= 65
        and scores["cost_adjusted_edge"] > 0
        and scores["tradeability"] >= 60
        and scores["entry_quality"] >= 60
        and scores["risk"] <= 60
        and plan_state == PLAN_PAPER_READY
    )


def _reason_codes(scores: dict[str, int], plan_state: str) -> tuple[str, ...]:
    reasons: list[str] = []
    if scores["tradeability"] < 45:
        reasons.append("poor_tradeability")
    if scores["entry_quality"] < 45:
        reasons.append("poor_entry_quality")
    if scores["risk"] >= 80:
        reasons.append("redline_risk")
    if plan_state != PLAN_PAPER_READY:
        reasons.append("plan_not_ready")
    if scores["cost_adjusted_edge"] <= 0:
        reasons.append("no_cost_adjusted_edge")
    return tuple(reasons)


def _wait_for(scores: dict[str, int], plan_state: str) -> str:
    waits: list[str] = []
    if scores["entry_quality"] < 45:
        waits.append("a better entry")
    if scores["tradeability"] < 45:
        waits.append("cleaner liquidity and execution conditions")
    if scores["risk"] >= 80:
        waits.append("risk compression or explicit full-loss boundaries")
    if plan_state != PLAN_PAPER_READY:
        waits.append("entry, invalidation, target, size, and exit logic")
    if not waits:
        waits.append("continued evidence and price-response confirmation")
    return "Wait for " + "; ".join(waits) + "."


def _plan_state(value: int) -> str:
    if value >= 70:
        return PLAN_PAPER_READY
    if value >= 30:
        return PLAN_DRAFT
    return PLAN_NOT_PLANNED


def _verdict(
    scores: dict[str, int],
    *,
    risk_class: str,
    plan_state: str,
    verdict: str,
    summary: str,
    wait_for: str,
    can_present: bool,
    reasons: tuple[str, ...],
) -> TradeReadinessVerdict:
    return TradeReadinessVerdict(
        scores=scores,
        risk_class=risk_class,
        plan_readiness=plan_state,
        verdict=verdict,
        public_summary=summary,
        professional_wait_for=wait_for,
        can_present_as_trade_idea=can_present,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def _score(value: int | float) -> int:
    return max(0, min(100, round(float(value))))


def _signed_score(value: int | float) -> int:
    return max(-100, min(100, round(float(value))))
