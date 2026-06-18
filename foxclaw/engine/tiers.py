"""The decision-tier vocabulary — defined exactly ONCE (resolves pin P9).

In v1 the tier set ``block / reduce / observe / allow / allow_boosted`` and its
``0 / .5 / .75 / 1 / 1.2`` multipliers were spelled out **three independent times**:
in ``bayesian_edge.decision_label()``, in the scoreboard builder's per-setup
``decision``, and in the pre-decision gate. Three owners of one vocabulary is the
code-level form of the very hazard invariant #3 ("the edge enters ``final`` exactly
once") exists to prevent: the definitions can drift, and "what does *boost* mean / size"
ends up answered in three places.

This module is the single owner. Every other engine module — the shadow edge grader
(``edge.decision_label``), the scoreboard grader (``score.decision_tier``), and the
authority gate (``gate``) — imports the tier names and the multiplier map from here and
never re-spells them. The graders may legitimately differ in *how* evidence maps to a
tier (the edge grades from a posterior probability; the scoreboard grades from a
composite score) — what must not differ is the **vocabulary** and what each tier *means
for sizing*. That lives here.

Pure standard library. No I/O. Domain-neutral (invariant #4): a tier is a commitment
instruction, not a market concept.
"""

from __future__ import annotations

from typing import Final

# ── The canonical tier vocabulary ──────────────────────────────────────────────
# The five real tiers, ordered from "do nothing" to "commit hardest".
BLOCK: Final = "block"
REDUCE: Final = "reduce"
OBSERVE: Final = "observe"
ALLOW: Final = "allow"
ALLOW_BOOSTED: Final = "allow_boosted"

TIERS: Final[tuple[str, ...]] = (BLOCK, REDUCE, OBSERVE, ALLOW, ALLOW_BOOSTED)

# ── Commitment multipliers per tier ────────────────────────────────────────────
# How hard each tier says to commit, as a fraction of the raw size. These magnitudes
# are load-bearing and evidence-backed: the 1.2x boost earns its keep out-of-sample
# (see docs/decisions.md, 2026-06-16 "Boost suspicion RESOLVED").
MULTIPLIERS: Final[dict[str, float]] = {
    BLOCK: 0.00,
    REDUCE: 0.50,
    OBSERVE: 0.75,
    ALLOW: 1.00,
    ALLOW_BOOSTED: 1.20,
}

# The safe fallback tier when there is no usable evidence (unknown subject, stale or
# missing scoreboard): proceed, but with caution. Caution on thin data is always the
# safe direction.
FALLBACK_TIER: Final = OBSERVE


def multiplier_for(tier: str) -> float:
    """The commitment multiplier for a tier, falling back to the cautious tier's
    multiplier for any unrecognized label (never raises — an unknown tier must not be
    treated as full size).
    """
    return MULTIPLIERS.get(tier, MULTIPLIERS[FALLBACK_TIER])


def suppress_boost_if_thin(tier: str, n: float, *, min_n: float) -> str:
    """Never BOOST on a thin sample — over-confidence is the risk a small n cannot earn.

    A ``allow_boosted`` on fewer than ``min_n`` observations is demoted to the cautious
    fallback tier. Every other tier (including ``block``) is returned unchanged: caution
    on thin data is the safe direction, so a catastrophic small-sample subject must stay
    blocked, not relaxed. This is a tier-level safety rule, so it lives with the tiers —
    the gate and any other consumer apply the one definition rather than re-deriving it.
    """
    if tier == ALLOW_BOOSTED and n < min_n:
        return FALLBACK_TIER
    return tier
