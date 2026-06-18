"""Unit tests for the gate + scoreboard scoring + the single tier vocabulary (P9).

Covers: the tier vocabulary has one owner (the multiplier map + boost-suppression live in
``engine.tiers`` and every grader/consumer uses it); the scoreboard grader's tier ladder,
shrinkage, and trust tiers; the gate's safe fallbacks, min-N boost suppression, and the
fact that it applies — never re-derives — the tier. Also the market setup-key split.
"""
from __future__ import annotations

import pytest

from foxclaw.adapters.market import setup_key
from foxclaw.engine import gate
from foxclaw.engine import score
from foxclaw.engine import tiers
from foxclaw.engine.edge import BayesianEdge, Observation


# --- tiers: the single vocabulary (P9) --------------------------------------

def test_multiplier_map_is_the_canonical_set():
    assert tiers.MULTIPLIERS == {
        "block": 0.00,
        "reduce": 0.50,
        "observe": 0.75,
        "allow": 1.00,
        "allow_boosted": 1.20,
    }


def test_multiplier_for_unknown_tier_falls_back_to_cautious_not_full():
    # An unrecognized tier must never be treated as full size.
    assert tiers.multiplier_for("not_a_real_tier") == tiers.MULTIPLIERS[tiers.OBSERVE]
    assert tiers.multiplier_for("not_a_real_tier") < 1.0


def test_suppress_boost_only_touches_boost_on_thin_n():
    assert tiers.suppress_boost_if_thin("allow_boosted", n=2, min_n=5) == "observe"
    # at/above the threshold, the boost stands
    assert tiers.suppress_boost_if_thin("allow_boosted", n=5, min_n=5) == "allow_boosted"
    # every other tier is untouched regardless of n — a thin block stays blocked
    for t in ("block", "reduce", "observe", "allow"):
        assert tiers.suppress_boost_if_thin(t, n=1, min_n=5) == t


def test_all_graders_speak_the_one_vocabulary():
    # edge grader, scoreboard grader, and the tier set agree on the label universe.
    assert set(tiers.TIERS) == {"block", "reduce", "observe", "allow", "allow_boosted"}
    edge = BayesianEdge("arm")
    assert edge.decision_label() in tiers.TIERS
    assert score.decision_tier(0.7, n=20, mean_reward=0.02) in tiers.TIERS


# --- score: trust tiers -----------------------------------------------------

@pytest.mark.parametrize("n,expected", [
    (0, "no_data"), (2, "no_data"),
    (3, "thin"), (9, "thin"),
    (10, "developing"), (29, "developing"),
    (30, "established"), (100, "established"),
])
def test_trust_tier_thresholds(n, expected):
    assert score.trust_tier(n) == expected


# --- score: composite score + shrinkage -------------------------------------

def test_composite_score_shrinks_to_neutral_on_thin_sample():
    # A perfect record on n=1 must stay near neutral 0.5 (can't earn a confident score).
    thin = score.composite_score(success_rate=1.0, reward_factor=3.0, n=1)
    assert abs(thin - 0.5) < 0.02
    # The same record at full sample earns close to the raw 1.0.
    full = score.composite_score(success_rate=1.0, reward_factor=3.0, n=30)
    assert full > 0.95
    assert full > thin


def test_composite_score_is_bounded():
    assert 0.0 <= score.composite_score(0.0, 0.0, 30) <= 1.0
    assert 0.0 <= score.composite_score(1.0, 99.0, 30) <= 1.0


# --- score: decision tier ladder --------------------------------------------

def test_decision_tier_thin_sample_observes():
    assert score.decision_tier(score=0.9, n=2, mean_reward=0.5) == "observe"


def test_decision_tier_catastrophe_blocks_even_on_small_sample():
    # n>=3 but catastrophic average reward -> block (the small-sample catastrophe catch).
    assert score.decision_tier(score=0.6, n=4, mean_reward=-0.10) == "block"


def test_decision_tier_weak_score_on_trusted_sample_blocks():
    assert score.decision_tier(score=0.30, n=15, mean_reward=0.0) == "block"


def test_decision_tier_net_negative_mediocre_blocks():
    assert score.decision_tier(score=0.44, n=15, mean_reward=-0.001) == "block"


def test_decision_tier_mediocre_reduces():
    assert score.decision_tier(score=0.40, n=15, mean_reward=0.02) == "reduce"


def test_decision_tier_strong_on_trusted_boosts():
    assert score.decision_tier(score=0.70, n=15, mean_reward=0.02) == "allow_boosted"


def test_decision_tier_strong_but_thin_only_allows_not_boosts():
    # strong score but n below MIN_SAMPLE_TRUST -> allow, not boost (the score grader's
    # own n-guard; the gate's suppression is a second, independent guard)
    assert score.decision_tier(score=0.70, n=5, mean_reward=0.02) == "allow"


# --- gate: fallbacks --------------------------------------------------------

def test_gate_unavailable_scoreboard_falls_back_to_observe():
    v = gate.evaluate("src:BTC/USD:long", 0.8, None, scoreboard_ok=False,
                      unavailable_reason="scoreboard stale")
    assert v.tier == "observe"
    assert v.multiplier == 0.75
    assert v.adjusted_commitment == pytest.approx(0.6)
    assert "stale" in v.reason


def test_gate_unknown_subject_falls_back_to_observe():
    v = gate.evaluate("src:NEW/USD:long", 1.0, None)
    assert v.tier == "observe"
    assert v.multiplier == 0.75
    assert "no history" in v.reason


def test_gate_applies_graded_tier_and_scales():
    record = {"decision": "allow", "trades": 40, "score": 0.55, "trust_tier": "established"}
    v = gate.evaluate("src:BTC/USD:long", 0.8, record)
    assert v.tier == "allow"
    assert v.adjusted_commitment == pytest.approx(0.8)
    assert v.n == 40


def test_gate_block_holds_at_zero_regardless_of_n():
    record = {"decision": "block", "trades": 2, "score": 0.1, "trust_tier": "no_data"}
    v = gate.evaluate("src:BAD/USD:short", 1.0, record)
    assert v.tier == "block"
    assert v.adjusted_commitment == 0.0


def test_gate_suppresses_boost_on_thin_sample():
    record = {"decision": "allow_boosted", "trades": 3, "score": 0.7, "trust_tier": "thin"}
    v = gate.evaluate("src:BTC/USD:long", 1.0, record, min_n=5)
    assert v.tier == "observe"  # demoted
    assert v.multiplier == 0.75
    assert "suppressed" in v.reason


def test_gate_boost_stands_at_threshold():
    record = {"decision": "allow_boosted", "trades": 5, "score": 0.7, "trust_tier": "thin"}
    v = gate.evaluate("src:BTC/USD:long", 1.0, record, min_n=5)
    assert v.tier == "allow_boosted"
    assert v.multiplier == 1.20


def test_gate_does_not_regrade_a_bad_record_tier():
    # The gate trusts the grader's tier; it does not recompute from score. A record whose
    # stored tier disagrees with its score is still applied as graded (single grader).
    record = {"decision": "allow", "trades": 40, "score": 0.10, "trust_tier": "established"}
    v = gate.evaluate("s", 1.0, record)
    assert v.tier == "allow"  # NOT re-graded to block off the low score


# --- adapter: setup key -----------------------------------------------------

def test_setup_key_shape():
    assert setup_key("financialjuice_rss", "BTC/USD", "long") == "financialjuice_rss:BTC/USD:long"
