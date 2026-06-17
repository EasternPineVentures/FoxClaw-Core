"""foxclaw.engine — the domain-neutral decision pipeline (pure stdlib).

Ported so far (v0.1.4): the edge estimator and the diagnostic trust scorers.
Still to come: gate, score, ingest/parse, decide (see docs/engine_port_plan.md).
"""

from .edge import BayesianEdge, EdgeVerdict, Observation, beta_cdf, beta_ppf

__all__ = [
    "BayesianEdge",
    "Observation",
    "EdgeVerdict",
    "beta_cdf",
    "beta_ppf",
]
