"""Subject scoring — the neutral half of the v1 scoreboard builder.

``tools/setup_performance_summary.py`` did two separable things: it (a) *read* market
outcomes from the DB and filtered corrupt rows, then (b) turned each subject's aggregate
record into a **trust tier**, a **composite score**, and a **decision tier**. Part (b) is
pure decision math — it speaks success-rate / reward-factor / sample-size, never symbols
or PnL — so it lives here in ``engine/``. Part (a) (the SQL, the ``source:symbol:side``
key, and the corruption filters that encode invariant #8) is market-and-store-specific
and lives in ``adapters/market`` (invariant #4).

A "subject" is anything we score repeatedly from a track record: a trade setup, a
sourcing channel, a content format. The caller (the market adapter) computes the three
inputs below from its own outcomes and hands them in; this module never touches I/O.

The decision tier returned here is drawn from the single tier vocabulary in
``engine.tiers`` (resolves pin P9) — this module is the *scoreboard grader*, one of the
two graders that map evidence onto that shared vocabulary.

Pure standard library. No I/O. Domain-neutral (invariant #4).

Ported from v1 ``tools/setup_performance_summary.py`` (the ``_trust_tier`` /
``_score_setup`` / ``_decision_label`` core), renamed to neutral terms on the way in.
"""

from __future__ import annotations

from typing import Final

from .tiers import ALLOW, ALLOW_BOOSTED, BLOCK, OBSERVE, REDUCE

# Sample-size thresholds: how many scored observations before a subject earns trust.
MIN_SAMPLE_LIGHT: Final = 3    # below this: no_data, never graded beyond "observe"
MIN_SAMPLE_TRUST: Final = 10   # at/above this: tiers may block or boost
MIN_SAMPLE_FULL: Final = 30    # at/above this: full trust, no shrinkage

# A subject whose AVERAGE per-observation reward is worse than this is blocked even on a
# small sample — catches a catastrophic subject (e.g. a -50%/observation source) that the
# n>=MIN_SAMPLE_TRUST rules would otherwise let slip through as "allow".
CATASTROPHE_MEAN_REWARD: Final = -0.03

# How much of the composite score is the success rate vs the reward factor.
_SUCCESS_WEIGHT: Final = 0.5
_REWARD_WEIGHT: Final = 0.5
# The reward factor saturates at this multiple (a 3:1 gain/loss ratio scores full marks).
_REWARD_FACTOR_CAP: Final = 3.0
_NEUTRAL_SCORE: Final = 0.5


def trust_tier(n: int) -> str:
    """Coarse confidence label from sample size alone: how much history backs a subject.

    ``no_data`` (< LIGHT) → ``thin`` (< TRUST) → ``developing`` (< FULL) → ``established``.
    """
    if n < MIN_SAMPLE_LIGHT:
        return "no_data"
    if n < MIN_SAMPLE_TRUST:
        return "thin"
    if n < MIN_SAMPLE_FULL:
        return "developing"
    return "established"


def composite_score(success_rate: float, reward_factor: float, n: int) -> float:
    """0.0–1.0 composite quality score for a subject, shrunk toward neutral on thin data.

    ``raw = 0.5*success_rate + 0.5*min(reward_factor/3, 1)`` blends how *often* it pays
    off with how *favourably* (gains vs losses). The raw score is then shrunk toward the
    neutral 0.5 by ``min(n/MIN_SAMPLE_FULL, 1)`` — a small sample can't earn a confident
    score, so it stays near neutral until ~30 observations accrue (Bayesian shrinkage).
    """
    raw = _SUCCESS_WEIGHT * success_rate + _REWARD_WEIGHT * min(
        reward_factor / _REWARD_FACTOR_CAP, 1.0
    )
    weight = min(n / MIN_SAMPLE_FULL, 1.0)
    return round(_NEUTRAL_SCORE * (1.0 - weight) + raw * weight, 4)


def decision_tier(score: float, n: int, mean_reward: float) -> str:
    """Map a scored subject onto the shared decision-tier vocabulary (engine.tiers).

    The ladder, most-protective first:
      * thin sample (n < LIGHT)                              → observe (gather more)
      * catastrophic average reward (n >= LIGHT)             → block
      * weak score on a trusted sample (n >= TRUST)          → block
      * net-negative reward with a mediocre score (n>=TRUST) → block
      * mediocre score                                       → reduce
      * strong score on a trusted sample                     → allow_boosted
      * otherwise                                            → allow
    """
    if n < MIN_SAMPLE_LIGHT:
        return OBSERVE
    # Catastrophic average loss blocks even on a small sample.
    if mean_reward < CATASTROPHE_MEAN_REWARD and n >= MIN_SAMPLE_LIGHT:
        return BLOCK
    if score < 0.35 and n >= MIN_SAMPLE_TRUST:
        return BLOCK
    # Trusted subject that still loses despite an OK-ish success rate.
    if mean_reward < 0 and score < 0.45 and n >= MIN_SAMPLE_TRUST:
        return BLOCK
    if score < 0.45:
        return REDUCE
    if score >= 0.60 and n >= MIN_SAMPLE_TRUST:
        return ALLOW_BOOSTED
    return ALLOW
