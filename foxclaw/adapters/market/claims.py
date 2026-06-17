"""Market definition of a "well-formed claim" — the market adapter's domain rule.

Split out of v1 ``trustworthiness.py`` on the v2 port: the generic trustworthiness
estimator is domain-neutral and lives in ``foxclaw.engine.trust`` (invariant #4); this
is the *market's* definition of whether a claim is structurally sane, so it lives in the
adapter where market vocabulary (side, entry, stop, target) is allowed.

`foxclaw.engine.trust.Trustworthiness` consumes the bool|None this returns via
`ClaimQuality(well_formed=...)`; other domains supply their own well-formedness rule.
Pure computation — looks only at proposed levels, never at outcomes.
"""

from __future__ import annotations


def market_claim_well_formed(
    *,
    side: str,
    entry: float | None,
    stop: float | None,
    target: float | None,
    min_rr: float = 0.1,
    max_rr: float = 20.0,
) -> bool | None:
    """Is a market claim structurally sane? Looks only at the proposed LEVELS, never
    at what happened. None when there are no levels to judge (e.g. a headline feed).

    Sane = entry positive; any given stop/target on the correct side of entry for the
    side; and, when both present, a plausible risk/reward (not absurd like 1000:1).
    """
    s = str(side or "").strip().lower()
    if entry is None or entry <= 0 or s not in {"long", "short"}:
        return None
    if stop is None and target is None:
        return None  # nothing to assess -> exploratory, not penalized
    if stop is not None:
        if s == "long" and not stop < entry:
            return False
        if s == "short" and not stop > entry:
            return False
    if target is not None:
        if s == "long" and not target > entry:
            return False
        if s == "short" and not target < entry:
            return False
    if stop is not None and target is not None:
        risk = abs(entry - stop)
        reward = abs(target - entry)
        if risk <= 0:
            return False
        rr = reward / risk
        if rr < min_rr or rr > max_rr:
            return False
    return True
