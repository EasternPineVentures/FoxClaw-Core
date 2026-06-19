"""Market-facing risk labels mapped to the shared readiness vocabulary."""
from __future__ import annotations

from foxclaw.policy.risk_classification import (
    RISK_REJECT,
    RISK_RESEARCH,
    RISK_REDLINE,
    RISK_SPECULATIVE,
    RISK_STRUCTURED,
    RISK_TACTICAL,
    RISK_WATCH,
)


def classify_market_risk(*, risk_score: int, plan_ready: bool, tradeable: bool) -> str:
    """Classify market risk for display and policy checks."""
    score = max(0, min(100, int(risk_score)))
    if score >= 95:
        return RISK_REJECT
    if score >= 80:
        return RISK_REDLINE
    if score >= 65:
        return RISK_SPECULATIVE
    if not tradeable:
        return RISK_WATCH
    if plan_ready and score <= 45:
        return RISK_STRUCTURED
    if plan_ready:
        return RISK_TACTICAL
    return RISK_RESEARCH
