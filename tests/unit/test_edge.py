"""Unit tests for the Bayesian edge estimator (foxclaw.engine.edge).

Covers the minimum set from docs/engine_port_plan.md: Beta CDF/PPF correctness,
posterior updates, edge-probability threshold, commitment methods + exploration floor,
catastrophe veto, decision tiering, and recency weighting.
"""
from __future__ import annotations

import math

import pytest

from foxclaw.engine.edge import BayesianEdge, Observation, beta_cdf, beta_ppf


# --- Beta functions --------------------------------------------------------

def test_beta_cdf_uniform_is_identity():
    # Beta(1,1) is Uniform(0,1): CDF(x) == x.
    for x in (0.1, 0.25, 0.5, 0.75, 0.9):
        assert beta_cdf(x, 1.0, 1.0) == pytest.approx(x, abs=1e-6)


def test_beta_cdf_bounds_and_monotonic():
    assert beta_cdf(0.0, 2.0, 5.0) == 0.0
    assert beta_cdf(1.0, 2.0, 5.0) == 1.0
    prev = -1.0
    for i in range(0, 101):
        v = beta_cdf(i / 100.0, 2.0, 5.0)
        assert v >= prev - 1e-12  # non-decreasing
        prev = v


def test_beta_ppf_inverts_cdf():
    a, b = 3.0, 4.0
    for q in (0.05, 0.25, 0.5, 0.75, 0.95):
        x = beta_ppf(q, a, b)
        assert beta_cdf(x, a, b) == pytest.approx(q, abs=1e-3)


def test_beta_ppf_uniform_is_identity():
    for q in (0.1, 0.5, 0.9):
        assert beta_ppf(q, 1.0, 1.0) == pytest.approx(q, abs=1e-6)


# --- posterior + edge ------------------------------------------------------

def test_posterior_shifts_with_evidence():
    e = BayesianEdge("arm")
    base = e.posterior_success_prob()  # prior 2 -> 0.5
    assert base == pytest.approx(0.5)
    e.add_many([Observation(True, 0.02)] * 8)
    assert e.posterior_success_prob() > 0.5
    e2 = BayesianEdge("arm")
    e2.add_many([Observation(False, 0.02)] * 8)
    assert e2.posterior_success_prob() < 0.5


def test_probability_of_edge_high_for_winning_arm():
    e = BayesianEdge("winner")
    e.add_many([Observation(True, 0.03)] * 15 + [Observation(False, 0.01)] * 2)
    assert e.probability_of_edge() > 0.7


def test_effective_n_counts_observations():
    e = BayesianEdge("arm")
    e.add_many([Observation(True, 0.02)] * 3 + [Observation(False, 0.02)] * 2)
    assert e.effective_n == pytest.approx(5.0)


# --- commitment + safety ---------------------------------------------------

def test_thin_arm_gets_exploration_floor():
    e = BayesianEdge("new", min_observations=5.0, exploration_floor=0.75)
    e.add_many([Observation(True, 0.02)] * 2)  # below min_observations, not catastrophic
    assert e.commitment() >= 0.75


def test_catastrophic_arm_is_zeroed_not_floored():
    e = BayesianEdge("disaster", catastrophe_expected_value=-0.03)
    e.add_many([Observation(False, 0.5)] * 6)  # big losses, conservative EV very negative
    assert e.is_catastrophic()
    assert e.commitment() == 0.0


def test_commitment_within_bounds():
    e = BayesianEdge("arm", max_commitment=1.2)
    e.add_many([Observation(True, 0.03)] * 20)
    for method in ("prob", "kelly", "min"):
        c = e.commitment(method=method)
        assert 0.0 <= c <= 1.2


def test_commitment_min_is_le_components():
    e = BayesianEdge("arm")
    e.add_many([Observation(True, 0.03)] * 12 + [Observation(False, 0.01)] * 3)
    assert e.commitment(method="min") <= e.commitment(method="prob") + 1e-9
    assert e.commitment(method="min") <= e.commitment(method="kelly") + 1e-9


def test_invalid_method_raises():
    e = BayesianEdge("arm")
    e.add_many([Observation(True, 0.02)] * 10)
    with pytest.raises(ValueError):
        e.commitment(method="bogus")


# --- decision label tiers --------------------------------------------------

def test_decision_label_observe_when_thin():
    e = BayesianEdge("arm")
    e.add(Observation(True, 0.02))  # n < 3
    assert e.decision_label() == "observe"


def test_decision_label_block_on_catastrophe():
    e = BayesianEdge("arm")
    e.add_many([Observation(False, 0.5)] * 6)
    assert e.decision_label() == "block"


def test_decision_label_allow_for_strong_arm():
    e = BayesianEdge("arm")
    e.add_many([Observation(True, 0.03)] * 18 + [Observation(False, 0.01)] * 2)
    assert e.decision_label() in {"allow", "allow_boosted"}


# --- recency weighting -----------------------------------------------------

def test_recency_halves_old_evidence_weight():
    e = BayesianEdge("arm", half_life_days=10.0)
    e.add(Observation(True, 0.02, age_days=10.0))  # one half-life old -> weight 0.5
    assert e.effective_successes == pytest.approx(0.5, abs=1e-9)


def test_extra_weight_scales_evidence():
    e = BayesianEdge("arm")
    e.add(Observation(True, 0.02), weight=0.5)
    assert e.effective_successes == pytest.approx(0.5)


def test_verdict_is_serializable_shape():
    e = BayesianEdge("arm")
    e.add_many([Observation(True, 0.03)] * 10)
    v = e.verdict()
    assert v.arm == "arm"
    assert 0.0 <= v.prob_edge <= 1.0
    assert math.isfinite(v.expected_value)
    assert v.decision in {"observe", "block", "reduce", "allow", "allow_boosted"}
