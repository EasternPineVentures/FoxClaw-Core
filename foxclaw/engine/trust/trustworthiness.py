"""Source trustworthiness — how much to trust what a source SAYS, not whether it paid.

This is the Pass-3.5 redesign of source reliability, built to fix the Pass-3 finding
(see docs/source_reliability_math.md): an *outcome-rate* reliability is unsafe — it
conflates hit-rate with edge and, folded into the edge, relaxes blocks on the least
reliable sources.

Trustworthiness measures something the edge does NOT: is a source's *claim*
well-formed and honest — sane levels, plausible structure, parseable? A manipulated,
spammy, or careless source produces malformed claims; that shows up here, **independent
of market randomness**. A source can be perfectly trustworthy (clean claims) and still
have a losing edge, and vice-versa — the two signals are deliberately orthogonal.

Two safety rules (the whole reason Pass-3 failed without them):
  1. Trustworthiness is scored from CLAIM QUALITY, never from outcomes/returns.
  2. It may only REDUCE the size of an ALREADY-CLEARED setup — never weaken a block,
     never size up. See ``trust_haircut``.

Domain-neutral: a "claim" is any structured proposal a source emits; "well-formed"
is whatever sanity its domain defines. **Each domain supplies its own definition** —
the market's lives in ``foxclaw.adapters.market`` (``market_claim_well_formed``), NOT
here, so this module stays domain-neutral (invariant #4). Pure stdlib; reuses the Beta
functions from edge.

Ported from v1 ``src/grovecore/trustworthiness.py``; the market well-formedness helper
was split out to the market adapter on port.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..edge import beta_ppf


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


@dataclass(frozen=True)
class ClaimQuality:
    """One source claim, scored for well-formedness only (NOT outcome).

    well_formed: True (sane claim) / False (malformed) / None (cannot assess -> ignored).
    """
    well_formed: bool | None
    age_days: float = 0.0


@dataclass
class TrustVerdict:
    source_id: str
    n: float            # effective assessable claims
    well_formed: float  # effective well-formed count
    malformed: float    # effective malformed count
    rho_trust: float    # trust weight in [rho_floor, 1.0]
    status: str         # exploratory | low_trust | trusted | thin


class Trustworthiness:
    """Per-source trust from claim well-formedness. rho_trust in [floor, 1] (down-weight only).

    Mirrors the conservative-Beta shape of SourceReliability but the EVIDENCE is claim
    quality, not profit. A claim that cannot be assessed (no levels to judge) is
    ignored, not counted against the source.
    """

    def __init__(
        self,
        *,
        prior_good: float = 2.0,
        prior_bad: float = 2.0,
        half_life_days: float | None = None,
        rho_floor: float = 0.25,
        rho_unknown: float = 0.75,
        sample_target: float = 10.0,
        quantile: float = 0.25,
    ) -> None:
        self.prior_good = prior_good
        self.prior_bad = prior_bad
        self.half_life_days = half_life_days
        self.rho_floor = rho_floor
        self.rho_unknown = rho_unknown
        self.sample_target = sample_target
        self.quantile = quantile
        self._counts: dict[str, list[float]] = {}  # source -> [good_eff, bad_eff]

    def _weight(self, age_days: float) -> float:
        if not self.half_life_days or self.half_life_days <= 0 or age_days <= 0:
            return 1.0
        return 0.5 ** (age_days / self.half_life_days)

    def add(self, source_id: str, claim: ClaimQuality, *, weight: float = 1.0) -> None:
        if claim.well_formed is None:  # not assessable -> ignore, don't penalize
            return
        w = max(0.0, float(weight)) * self._weight(claim.age_days)
        if w <= 0:
            return
        bucket = self._counts.setdefault(str(source_id), [0.0, 0.0])
        bucket[0 if claim.well_formed else 1] += w

    def _rho(self, good: float, bad: float) -> float:
        n = good + bad
        rho_raw = beta_ppf(self.quantile, self.prior_good + good, self.prior_bad + bad)
        lam = min(n / self.sample_target, 1.0) if self.sample_target > 0 else 1.0
        rho = lam * rho_raw + (1.0 - lam) * self.rho_unknown
        return _clamp(rho, self.rho_floor, 1.0)

    def trust(self, source_id: str) -> float:
        c = self._counts.get(str(source_id))
        return self._rho(c[0], c[1]) if c else self.rho_unknown

    def _status(self, n: float, rho: float) -> str:
        if n < 3:
            return "thin"
        if rho <= self.rho_unknown - 0.10:
            return "low_trust"
        if rho >= 0.9:
            return "trusted"
        return "exploratory"

    def verdict(self, source_id: str) -> TrustVerdict:
        c = self._counts.get(str(source_id), [0.0, 0.0])
        good, bad = c[0], c[1]
        return TrustVerdict(
            source_id=str(source_id),
            n=round(good + bad, 4),
            well_formed=round(good, 4),
            malformed=round(bad, 4),
            rho_trust=round(self.trust(source_id), 6),
            status=self._status(good + bad, self.trust(source_id)),
        )

    def report(self) -> list[TrustVerdict]:
        return sorted((self.verdict(s) for s in self._counts), key=lambda v: -v.n)


# ── The safe application (the rule that makes Pass-3.5 safe) ─────────────────────

_BLOCK_DECISIONS = {"block", "block_paper_setup", "block_paper_source"}


def trust_haircut(base_commitment: float, base_decision: str, rho_trust: float) -> float:
    """Apply trustworthiness ONLY as a downward haircut on an already-cleared setup.

    - A blocked setup stays blocked (returns 0) — trust can NEVER un-block.
    - A cleared setup is multiplied by rho_trust in [0, 1] — trust can only REDUCE,
      never size up.

    This is the safety shape Pass-3 lacked: the block is decided on full evidence by
    the edge/gate; trust merely throttles what's already allowed.
    """
    if str(base_decision) in _BLOCK_DECISIONS:
        return 0.0
    return max(0.0, float(base_commitment)) * _clamp(float(rho_trust), 0.0, 1.0)
