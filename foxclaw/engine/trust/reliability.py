"""Source reliability — a living, domain-neutral replacement for stale source caps.

THE RULE (burned into the bark):
    rho_source WEIGHTS EVIDENCE. It does NOT directly cap the final action size.

That is the whole point. The old `source_overrides` were hand-set notional
ceilings that fought the per-setup gate (an allowed setup could still be capped by
a stale June number). This models, instead, *how much to trust a source's evidence*
when estimating edge — so a source that goes bad simply gets quieter, a source that
improves earns its weight back, and a new source is explored, not frozen out.

Two invariants keep this from becoming "source_overrides 2.0":
  1. It feeds EVIDENCE WEIGHT (S_eff / F_eff in the edge posterior), never final size.
  2. v1 only DOWN-weights: rho ∈ [rho_floor, 1.0], never > 1.0. Boosts come from the
     setup edge alone, so the "edge enters final exactly once" invariant survives.

Domain-neutral: a "source" is whoever produced a claim (an analyst, feed, agent,
node). Reliability is estimated from whether that source's claims later resolved
usefully. Markets are one adapter; nothing here is market-specific.

Math: Beta-Binomial posterior on "useful-evidence probability", read at a
conservative lower quantile (suspicious, but not frozen). Pure stdlib — reuses the
pure-Python Beta functions from edge. No I/O, no writes, no sizing.

Ported from v1 ``src/grovecore/source_reliability.py``. Per invariant #5 + the
decision log, this stays a SHADOW DIAGNOSTIC — it is not wired into live sizing
without the shadow-first ritual (invariant #2).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..edge import beta_ppf


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


@dataclass
class ReliabilityVerdict:
    source_id: str
    n: float                 # effective (possibly decayed) evidence count
    useful: float            # effective useful count
    harmful: float           # effective harmful count
    rho_mean: float          # posterior mean (context)
    rho_p25: float           # conservative lower-quantile posterior
    rho: float               # final reliability weight in [rho_floor, 1.0]
    status: str              # "exploratory" | "down_weighted" | "trusted" | "thin"


class SourceReliability:
    """Accumulate per-source (and per source+category) reliability from outcomes.

    add(source_id, useful=...) -> reliability(source_id[, category]) in [floor, 1].

    Parameters
    ----------
    prior_useful, prior_harmful : Beta prior pseudo-counts (default 2, 2 = neutral).
    half_life_days  : recency half-life; None disables decay.
    rho_floor       : a source is never fully silenced (default 0.25).
    rho_unknown     : weight for an unknown / thin source — explored, not trusted
                      (default 0.75).
    sample_target   : effective evidence at which we fully trust the local estimate
                      over the exploratory prior (default 10).
    quantile        : posterior quantile for reliability — lower = more suspicious
                      (default 0.25).
    """

    def __init__(
        self,
        *,
        prior_useful: float = 2.0,
        prior_harmful: float = 2.0,
        half_life_days: float | None = None,
        rho_floor: float = 0.25,
        rho_unknown: float = 0.75,
        sample_target: float = 10.0,
        quantile: float = 0.25,
    ) -> None:
        self.prior_useful = prior_useful
        self.prior_harmful = prior_harmful
        self.half_life_days = half_life_days
        self.rho_floor = rho_floor
        self.rho_unknown = rho_unknown
        self.sample_target = sample_target
        self.quantile = quantile
        # source_id -> [useful_eff, harmful_eff]
        self._global: dict[str, list[float]] = {}
        # (source_id, category) -> [useful_eff, harmful_eff]
        self._category: dict[tuple[str, str], list[float]] = {}

    # -- ingest -----------------------------------------------------------------
    def _weight(self, age_days: float) -> float:
        if not self.half_life_days or self.half_life_days <= 0 or age_days <= 0:
            return 1.0
        return 0.5 ** (age_days / self.half_life_days)

    def add(
        self,
        source_id: str,
        *,
        useful: bool,
        age_days: float = 0.0,
        category: str | None = None,
        weight: float = 1.0,
    ) -> None:
        w = max(0.0, float(weight)) * self._weight(age_days)
        if w <= 0:
            return
        idx = 0 if useful else 1
        g = self._global.setdefault(str(source_id), [0.0, 0.0])
        g[idx] += w
        if category:
            c = self._category.setdefault((str(source_id), str(category)), [0.0, 0.0])
            c[idx] += w

    # -- reliability ------------------------------------------------------------
    def _rho_from_counts(self, useful: float, harmful: float) -> float:
        """Conservative posterior reliability, shrunk toward the exploratory prior
        when evidence is thin. Always within [rho_floor, 1.0] — never a boost."""
        n = useful + harmful
        rho_raw = beta_ppf(self.quantile, self.prior_useful + useful, self.prior_harmful + harmful)
        lam = min(n / self.sample_target, 1.0) if self.sample_target > 0 else 1.0
        rho = lam * rho_raw + (1.0 - lam) * self.rho_unknown
        return _clamp(rho, self.rho_floor, 1.0)

    def reliability(self, source_id: str, category: str | None = None) -> float:
        """Reliability weight for a source (optionally within a category).

        Hierarchical: a category-specific estimate is shrunk toward the source's
        global estimate by how much category evidence exists, so a source is not
        condemned everywhere for one bad lane, nor trusted everywhere for one good
        lane. An unknown source is exploratory (rho_unknown), not zero.
        """
        g = self._global.get(str(source_id))
        if category is not None:
            c = self._category.get((str(source_id), str(category)))
            if c:
                rho_cat = self._rho_from_counts(c[0], c[1])
                rho_glob = self._rho_from_counts(g[0], g[1]) if g else self.rho_unknown
                n_cat = c[0] + c[1]
                lam = min(n_cat / self.sample_target, 1.0) if self.sample_target > 0 else 1.0
                return _clamp(lam * rho_cat + (1.0 - lam) * rho_glob, self.rho_floor, 1.0)
        if g:
            return self._rho_from_counts(g[0], g[1])
        return self.rho_unknown  # unknown source: explore, don't trust or freeze

    def _status(self, n: float, rho: float) -> str:
        if n < 3:
            return "thin"
        if rho <= self.rho_unknown - 0.10:
            return "down_weighted"
        if rho >= 0.9:
            return "trusted"
        return "exploratory"

    def verdict(self, source_id: str) -> ReliabilityVerdict:
        g = self._global.get(str(source_id), [0.0, 0.0])
        useful, harmful = g[0], g[1]
        n = useful + harmful
        a, b = self.prior_useful + useful, self.prior_harmful + harmful
        rho = self.reliability(source_id)
        return ReliabilityVerdict(
            source_id=str(source_id),
            n=round(n, 4),
            useful=round(useful, 4),
            harmful=round(harmful, 4),
            rho_mean=round(a / (a + b), 6),
            rho_p25=round(beta_ppf(self.quantile, a, b), 6),
            rho=round(rho, 6),
            status=self._status(n, rho),
        )

    def report(self) -> list[ReliabilityVerdict]:
        return sorted(
            (self.verdict(sid) for sid in self._global),
            key=lambda v: -v.n,
        )

    def category_reliabilities(self, source_id: str) -> list[tuple[str, float, float]]:
        """Per-lane breakdown for a source: [(category, n, rho)] sorted by evidence.

        This is what stops global reliability from being a blunt instrument: a
        source mediocre overall can still have an excellent lane, and that lane
        must not inherit the source's average penalty (the very 'source_overrides'
        failure mode). The per-setup gate / category reliability is what protects it.
        """
        out: list[tuple[str, float, float]] = []
        for (sid, cat), counts in self._category.items():
            if sid == str(source_id):
                n = counts[0] + counts[1]
                out.append((cat, n, self.reliability(source_id, category=cat)))
        return sorted(out, key=lambda t: -t[1])
