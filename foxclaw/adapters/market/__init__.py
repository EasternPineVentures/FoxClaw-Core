"""foxclaw.adapters.market — OHLCV / venue / price feeds, and market domain rules.

The ONLY place market vocabulary lives (invariant #4). Holds the market's definition of a
well-formed claim (consumed by the domain-neutral engine.trust.Trustworthiness), the
``source:symbol:side`` subject key, and the scoreboard builder that translates closed paper
outcomes into the neutral inputs the engine grades (the full evidence → edge → gate chain).
"""

from .claims import market_claim_well_formed
from .scoreboard import (
    assess_setup,
    build_scoreboard,
    clean_rows,
    edge_verdict_for,
    observations_by_subject,
)
from .setup import setup_key

__all__ = [
    "market_claim_well_formed",
    "setup_key",
    "build_scoreboard",
    "assess_setup",
    "edge_verdict_for",
    "observations_by_subject",
    "clean_rows",
]
