"""Bayesian edge estimation — domain-neutral core of FoxClaw's decision matrix.

FoxClaw is a general adaptive decision matrix, not a trading-only tool. The
question this module answers is deliberately domain-free:

    "Given a stream of past outcomes for some CATEGORY of decision, what is the
     probability that committing to it has positive expected value, and how hard
     should we commit?"

A *category* (called an ``arm`` here, from the bandit literature) is anything we
can decide repeatedly and later score: a trade setup, a sneaker flip, a card buy,
a sourcing channel. Each past outcome is one ``Observation``:

    success   : bool   — did it pay off?
    magnitude : float  — POSITIVE fraction of stake won (if success) or lost (if not)
    age_days  : float  — how long ago (for optional recency weighting)

Nothing in this file mentions trading. The trading-specific mapping (closed paper
positions -> Observations) lives in the adapter that calls this, keeping the core
reusable across every domain FoxClaw grows into.

Math: Beta-Binomial posterior on the success probability (Bayes, 1763) combined
with the Kelly criterion (1956) for commitment sizing. Pure standard library —
no numpy/scipy — so it runs anywhere the organism runs.

Safety: pure computation. No I/O, no network, no orders, no funds movement.

Ported from v1 ``src/grovecore/bayesian_edge.py`` unchanged (already pure + neutral).
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import median
from typing import Iterable


# ── Pure-Python regularized incomplete beta (Beta CDF) and its inverse ──────────
# Lets us compute P(success_prob > threshold) and posterior percentiles without
# numpy/scipy. Continued-fraction method (Numerical Recipes, "betacf"/"betai").

_BETA_EPS = 3.0e-12
_BETA_FPMIN = 1.0e-300
_BETA_MAXIT = 300


def _betacf(a: float, b: float, x: float) -> float:
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < _BETA_FPMIN:
        d = _BETA_FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, _BETA_MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _BETA_FPMIN:
            d = _BETA_FPMIN
        c = 1.0 + aa / c
        if abs(c) < _BETA_FPMIN:
            c = _BETA_FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _BETA_FPMIN:
            d = _BETA_FPMIN
        c = 1.0 + aa / c
        if abs(c) < _BETA_FPMIN:
            c = _BETA_FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _BETA_EPS:
            break
    return h


def beta_cdf(x: float, a: float, b: float) -> float:
    """Regularized incomplete beta I_x(a, b) = CDF of Beta(a, b) at x."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_bt = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log(1.0 - x)
    )
    bt = math.exp(ln_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def beta_ppf(q: float, a: float, b: float, *, tol: float = 1e-9) -> float:
    """Inverse CDF (quantile) of Beta(a, b) via bisection on beta_cdf."""
    if q <= 0.0:
        return 0.0
    if q >= 1.0:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if beta_cdf(mid, a, b) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


# ── Observation + estimator ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Observation:
    success: bool
    magnitude: float          # positive fraction of stake (reward if success, else cost)
    age_days: float = 0.0     # 0 => full weight (no recency decay)


@dataclass
class EdgeVerdict:
    """The estimator's answer for one arm."""
    arm: str
    n: float                  # effective (possibly decayed) observation count
    prob_edge: float          # P(expected value > 0 | data)
    expected_value: float     # point estimate of mean outcome (fraction of stake)
    kelly_fraction: float     # conservative fractional-Kelly commitment in [0, cap]
    commitment: float         # final size multiplier in [0, max_commitment] (selected method)
    commitment_prob: float    # probability-mapped commitment (for shadow comparison)
    commitment_kelly: float   # Kelly-mapped commitment (for shadow comparison)
    decision: str             # discrete label compatible with the existing gate
    reward: float             # shrunk typical reward magnitude
    cost: float               # shrunk typical cost magnitude


class BayesianEdge:
    """Estimate edge + commitment for ONE arm from its outcome history.

    Parameters mirror the design's hyperparameters but are domain-neutral:

    prior_strength      pseudo-observations pulling the success prob toward 0.5
                        (alpha = beta = prior_strength / 2). Default 2 = mildly
                        skeptical: one success out of one observation lands at 0.6,
                        not 0.67.
    half_life_days      recency: an outcome this many days old counts half. None
                        (default) disables decay (every outcome counts fully).
    min_observations    below this effective count an arm is "thin" — we apply the
                        exploration floor so new arms still get tried (explore),
                        never silently frozen out at zero (which would stop the
                        organism from ever learning a new arm).
    exploration_floor   the commitment a thin, non-catastrophic arm still receives.
    risk_aversion       fractional-Kelly factor (0.25 = quarter-Kelly), the
                        standard safety haircut for acting under uncertainty.
    kelly_cap           hard cap on the Kelly fraction per decision.
    max_commitment      ceiling on the output multiplier (1.2 mirrors the gate's
                        allow_boosted).
    """

    def __init__(
        self,
        arm: str = "",
        *,
        prior_strength: float = 2.0,
        half_life_days: float | None = None,
        min_observations: float = 5.0,
        exploration_floor: float = 0.75,
        risk_aversion: float = 0.25,
        kelly_cap: float = 0.25,
        max_commitment: float = 1.2,
        catastrophe_expected_value: float = -0.03,
        magnitude: str = "mean",
    ) -> None:
        self.arm = arm
        self.alpha_prior = prior_strength / 2.0
        self.beta_prior = prior_strength / 2.0
        self.half_life_days = half_life_days
        self.min_observations = min_observations
        self.exploration_floor = exploration_floor
        self.risk_aversion = risk_aversion
        self.kelly_cap = kelly_cap
        self.max_commitment = max_commitment
        self.catastrophe_expected_value = catastrophe_expected_value
        # "mean" is tail-aware (rare large losses count) and is correct when the
        # caller has already corruption-filtered its inputs — which FoxClaw's
        # adapter does (RETURN_SANITY_CAP, entry-outlier). "median" is available
        # for noisy/unfiltered domains but HIDES tail risk, so it is not default.
        self.magnitude = magnitude
        # (weight, magnitude) pairs
        self._successes: list[tuple[float, float]] = []
        self._failures: list[tuple[float, float]] = []
        # domain-global fallbacks for shrinkage (set via set_reference_magnitudes)
        self._ref_reward = 0.02
        self._ref_cost = 0.01

    # -- ingest -----------------------------------------------------------------
    def _weight(self, age_days: float) -> float:
        if not self.half_life_days or self.half_life_days <= 0 or age_days <= 0:
            return 1.0
        # age_days is the AGE of the observation (now - observed_at), NOT an
        # absolute epoch day — that distinction is the bug we are not repeating.
        return 0.5 ** (age_days / self.half_life_days)

    def add(self, obs: Observation, *, weight: float = 1.0) -> None:
        """Add an outcome. ``weight`` is an extra evidence weight in [0, 1] on top
        of recency — e.g. a source-reliability factor (rho_source). A low weight
        makes this outcome count less toward the posterior (less confident edge),
        which is how source reliability folds in WITHOUT capping the final size.
        """
        w = self._weight(obs.age_days) * max(0.0, float(weight))
        mag = abs(float(obs.magnitude))
        if obs.success:
            self._successes.append((w, mag))
        else:
            self._failures.append((w, mag))

    def add_many(self, observations: Iterable[Observation], *, weight: float = 1.0) -> None:
        for obs in observations:
            self.add(obs, weight=weight)

    def set_reference_magnitudes(self, *, reward: float, cost: float) -> None:
        """Domain-global typical reward/cost, used to shrink thin arms toward
        sane magnitudes instead of trusting one extreme observation."""
        if reward > 0:
            self._ref_reward = float(reward)
        if cost > 0:
            self._ref_cost = float(cost)

    # -- posterior --------------------------------------------------------------
    @property
    def effective_successes(self) -> float:
        return sum(w for w, _ in self._successes)

    @property
    def effective_failures(self) -> float:
        return sum(w for w, _ in self._failures)

    @property
    def effective_n(self) -> float:
        return self.effective_successes + self.effective_failures

    def _alpha_post(self) -> float:
        return self.alpha_prior + self.effective_successes

    def _beta_post(self) -> float:
        return self.beta_prior + self.effective_failures

    def posterior_success_prob(self) -> float:
        return self._alpha_post() / (self._alpha_post() + self._beta_post())

    def _shrunk_magnitude(self, pairs: list[tuple[float, float]], reference: float) -> float:
        """Typical magnitude, shrunk toward the domain reference when the arm is
        thin. Uses the (weight-aware) MEAN by default so rare large losses count
        toward expected value — the median would hide exactly the tail risk that
        determines whether a setup is really net-positive."""
        if not pairs:
            return reference
        total_w = sum(w for w, _ in pairs)
        if total_w <= 0:
            return reference
        if self.magnitude == "median":
            typical = median([m for _, m in pairs])
        else:
            typical = sum(w * m for w, m in pairs) / total_w
        shrink = min(1.0, total_w / self.min_observations)
        return shrink * typical + (1.0 - shrink) * reference

    def reward(self) -> float:
        return self._shrunk_magnitude(self._successes, self._ref_reward)

    def cost(self) -> float:
        return self._shrunk_magnitude(self._failures, self._ref_cost)

    def probability_of_edge(self) -> float:
        """P(expected value > 0 | data).

        EV = reward*p - cost*(1-p) = (reward+cost)*p - cost > 0  <=>  p > cost/(reward+cost).
        With p ~ Beta(alpha_post, beta_post), that tail probability is 1 - CDF(threshold).
        """
        r, c = self.reward(), self.cost()
        if r <= 0 or c <= 0:
            return 0.5
        threshold = c / (r + c)
        return 1.0 - beta_cdf(threshold, self._alpha_post(), self._beta_post())

    def expected_value(self, *, conservative: bool = False) -> float:
        r, c = self.reward(), self.cost()
        # conservative uses the 25th-percentile posterior success prob (acting
        # under uncertainty errs low), addressing the design's Pass 5/7.
        if conservative and self.effective_n > 0:
            p = beta_ppf(0.25, self._alpha_post(), self._beta_post())
        else:
            p = self.posterior_success_prob()
        return r * p - c * (1.0 - p)

    def kelly(self) -> float:
        """Conservative fractional Kelly commitment fraction in [0, kelly_cap].

        Uses the 25th-percentile posterior success prob (not the mean), so the
        haircut for uncertainty is built in before risk_aversion is applied.
        """
        r, c = self.reward(), self.cost()
        if r <= 0 or c <= 0 or self.effective_n <= 0:
            return 0.0
        p = beta_ppf(0.25, self._alpha_post(), self._beta_post())
        f = (p * r - (1.0 - p) * c) / (r * c)
        f *= self.risk_aversion
        return max(0.0, min(self.kelly_cap, f))

    # -- output -----------------------------------------------------------------
    def commitment_prob(self) -> float:
        """Interpretable commitment: linear in P(edge), 0.5->0 .. 1.0->max."""
        p = self.probability_of_edge()
        return min(self.max_commitment, max(0.0, (p - 0.5) * 2.0) * self.max_commitment)

    def commitment_kelly(self) -> float:
        """Kelly-fraction commitment rescaled into the commitment range."""
        if self.kelly_cap <= 0:
            return 0.0
        return min(self.max_commitment, (self.kelly() / self.kelly_cap) * self.max_commitment)

    def is_catastrophic(self) -> bool:
        return (
            self.effective_n >= 3
            and self.expected_value(conservative=True) < self.catastrophe_expected_value
        )

    def commitment(self, *, method: str = "min") -> float:
        """Size multiplier in [0, max_commitment].

        method='prob'  — interpretable: linear in P(edge).
        method='kelly' — conservative fractional Kelly, rescaled.
        method='min'   — min(prob, kelly): "probability must like it AND Kelly
                         must not hate it". The conservative default — neither a
                         confident-but-tiny-edge nor a fat-payoff-but-uncertain
                         arm alone can size up.

        Exploration floor: a THIN, non-catastrophic arm receives at least
        exploration_floor so the organism keeps gathering data on it (a learning
        system that zeros every unknown can never learn a new arm). A catastrophic
        arm (conservative EV below the catastrophe threshold) is never floored.
        """
        if self.is_catastrophic():
            return 0.0
        if method == "prob":
            raw = self.commitment_prob()
        elif method == "kelly":
            raw = self.commitment_kelly()
        elif method == "min":
            raw = min(self.commitment_prob(), self.commitment_kelly())
        else:
            raise ValueError("method must be 'prob', 'kelly', or 'min'")

        if self.effective_n < self.min_observations:
            return max(self.exploration_floor, raw)
        return raw

    def decision_label(self) -> str:
        """Discrete label compatible with the existing gate vocabulary, so this
        can shadow the current scoreboard decision for apples-to-apples logging.
        """
        if self.effective_n < 3:
            return "observe"
        if self.expected_value(conservative=True) < self.catastrophe_expected_value:
            return "block"
        p = self.probability_of_edge()
        if p < 0.50:
            return "block"
        if p < 0.60:
            return "reduce"
        if p >= 0.85 and self.effective_n >= 10:
            return "allow_boosted"
        if p < 0.70:
            return "observe"
        return "allow"

    def verdict(self, *, method: str = "min") -> EdgeVerdict:
        return EdgeVerdict(
            arm=self.arm,
            n=round(self.effective_n, 4),
            prob_edge=round(self.probability_of_edge(), 6),
            expected_value=round(self.expected_value(), 6),
            kelly_fraction=round(self.kelly(), 6),
            commitment=round(self.commitment(method=method), 6),
            commitment_prob=round(self.commitment(method="prob"), 6),
            commitment_kelly=round(self.commitment(method="kelly"), 6),
            decision=self.decision_label(),
            reward=round(self.reward(), 6),
            cost=round(self.cost(), 6),
        )
