"""foxclaw.engine — the domain-neutral decision pipeline (pure stdlib).

Ported so far (v0.1.5): the edge estimator, the diagnostic trust scorers, and the
gate + scoreboard scoring — with the decision-tier vocabulary owned in one place
(``engine.tiers``; resolves pin P9). Still to come: ingest/parse, decide, and the
market scoreboard *builder* adapter (see docs/engine_port_plan.md).
"""

from .edge import BayesianEdge, EdgeVerdict, Observation, beta_cdf, beta_ppf
from .gate import GateVerdict, evaluate
from .score import composite_score, decision_tier, trust_tier
from .tiers import MULTIPLIERS, TIERS, multiplier_for, suppress_boost_if_thin

__all__ = [
    # edge
    "BayesianEdge",
    "Observation",
    "EdgeVerdict",
    "beta_cdf",
    "beta_ppf",
    # tiers (the single decision-tier vocabulary — P9)
    "TIERS",
    "MULTIPLIERS",
    "multiplier_for",
    "suppress_boost_if_thin",
    # score (the scoreboard grader)
    "trust_tier",
    "composite_score",
    "decision_tier",
    # gate (the edge authority)
    "evaluate",
    "GateVerdict",
]
