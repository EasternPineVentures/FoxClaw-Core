"""The decision gate — the single edge authority, as neutral commitment logic.

Invariant #3: "the edge enters ``final`` exactly once", and the gate is that one place
(live on A2 since 2026-06-16). v1's ``tools/pre_decision_gate.py`` mixed that authority
with market I/O: it loaded a JSON scoreboard, built a ``source:symbol:side`` key, and
checked file mtime for staleness. Those are adapter concerns. What remains here is the
pure decision: given a subject's already-graded record (or the fact that we have none),
turn a raw commitment into a final tier + multiplier.

The market adapter owns the I/O half — building the subject key, loading the scoreboard,
and deciding whether it is fresh — then calls :func:`evaluate`. The tier vocabulary and
the multiplier map come from ``engine.tiers`` (resolves pin P9): the gate applies the one
definition, it does not re-spell it.

What this gate does NOT do: it does not *re-grade* the subject. The scoreboard grader
(``engine.score.decision_tier``) already chose the subject's tier from its track record;
the gate only (a) falls back safely when there is no usable record, and (b) applies the
min-sample boost-suppression safety rule. Re-deriving the tier here would be a second
grader — the exact multi-owner hazard P9/invariant #3 forbid.

Pure standard library. No I/O. Domain-neutral (invariant #4).

Ported from v1 ``tools/pre_decision_gate.py`` (the ``evaluate`` core), with the scoreboard
loading / freshness / market-key concerns lifted out to ``adapters/market``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping

from .tiers import FALLBACK_TIER, multiplier_for, suppress_boost_if_thin

# Minimum observations before a boost is allowed to stand (see tiers.suppress_boost_if_thin).
MIN_N_FOR_EXTREMES: Final = 5


@dataclass(frozen=True)
class GateVerdict:
    """The gate's ruling on one proposed commitment."""

    subject: str
    tier: str
    multiplier: float
    raw_commitment: float
    adjusted_commitment: float
    reason: str
    score: float | None
    n: int
    trust_tier: str


def _verdict(
    subject: str,
    tier: str,
    raw_commitment: float,
    reason: str,
    *,
    score: float | None,
    n: int,
    trust_tier: str,
) -> GateVerdict:
    multiplier = multiplier_for(tier)
    return GateVerdict(
        subject=subject,
        tier=tier,
        multiplier=multiplier,
        raw_commitment=round(float(raw_commitment), 6),
        adjusted_commitment=round(float(raw_commitment) * multiplier, 6),
        reason=reason,
        score=round(score, 4) if score is not None else None,
        n=n,
        trust_tier=trust_tier,
    )


def evaluate(
    subject: str,
    raw_commitment: float,
    record: Mapping[str, Any] | None,
    *,
    scoreboard_ok: bool = True,
    unavailable_reason: str = "scoreboard unavailable",
    min_n: int = MIN_N_FOR_EXTREMES,
) -> GateVerdict:
    """Rule on a proposed commitment to ``subject``.

    Parameters
    ----------
    subject:
        Opaque subject id (the market adapter builds the real key, e.g. source:symbol:side).
    raw_commitment:
        The pre-gate commitment to scale (the upstream estimate).
    record:
        The subject's graded scoreboard row, or ``None`` if it has no history. When given,
        it must carry the keys the scoreboard grader writes: ``decision`` (a tier),
        ``score``, ``trades`` (n), and ``trust_tier``.
    scoreboard_ok:
        ``False`` when the adapter judged the scoreboard missing or stale — both collapse
        to the safe fallback tier here. ``unavailable_reason`` explains which.
    min_n:
        Boost-suppression threshold (never boost on a thinner sample than this).

    Fallbacks are always the cautious tier (``observe``), never full size — caution on
    absent evidence is the safe direction.
    """
    # Scoreboard unusable → safe fallback, regardless of the subject.
    if not scoreboard_ok:
        return _verdict(
            subject, FALLBACK_TIER, raw_commitment,
            f"{unavailable_reason} — safe fallback to {FALLBACK_TIER}",
            score=None, n=0, trust_tier="no_data",
        )

    # No history for this subject → safe fallback.
    if record is None:
        return _verdict(
            subject, FALLBACK_TIER, raw_commitment,
            f"subject '{subject}' has no history — safe fallback to {FALLBACK_TIER}",
            score=None, n=0, trust_tier="no_data",
        )

    graded_tier = str(record.get("decision") or FALLBACK_TIER)
    n = int(record.get("trades") or 0)
    score = record.get("score")
    score = float(score) if score is not None else None
    trust_tier = str(record.get("trust_tier") or "no_data")

    # Apply the one boost-suppression rule (never boost on a thin sample). A block always
    # holds regardless of n.
    final_tier = suppress_boost_if_thin(graded_tier, n, min_n=min_n)
    if final_tier != graded_tier:
        reason = (
            f"graded={graded_tier} n={n} score="
            f"{score:.3f}" if score is not None else f"graded={graded_tier} n={n}"
        )
        reason += f"; boost suppressed to {final_tier} (n={n} < min_n={min_n})"
    else:
        reason = (
            f"graded={graded_tier} n={n} score={score:.3f}"
            if score is not None
            else f"graded={graded_tier} n={n}"
        )

    return _verdict(
        subject, final_tier, raw_commitment, reason,
        score=score, n=n, trust_tier=trust_tier,
    )
