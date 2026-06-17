"""Unit tests for the diagnostic trust scorers and the market-claim adapter.

Covers: reliability + trustworthiness stay down-weight-only (invariant #5), unknown
sources are exploratory (not frozen), trust_haircut never un-blocks / only reduces,
unassessable claims are ignored, and the split-out market well-formedness rule.
"""
from __future__ import annotations

import pytest

from foxclaw.adapters.market import market_claim_well_formed
from foxclaw.engine.trust import (
    ClaimQuality,
    SourceReliability,
    Trustworthiness,
    trust_haircut,
)


# --- reliability (rho_source) ----------------------------------------------

def test_reliability_unknown_source_is_exploratory():
    r = SourceReliability(rho_unknown=0.75)
    assert r.reliability("never_seen") == 0.75


def test_reliability_never_exceeds_one():
    r = SourceReliability()
    for _ in range(50):
        r.add("great", useful=True)
    assert r.reliability("great") <= 1.0


def test_reliability_stays_above_floor():
    r = SourceReliability(rho_floor=0.25)
    for _ in range(50):
        r.add("awful", useful=False)
    assert r.reliability("awful") >= 0.25


def test_bad_source_downweighted_below_unknown():
    r = SourceReliability(rho_unknown=0.75)
    for _ in range(20):
        r.add("bad", useful=False)
    assert r.reliability("bad") < 0.75


def test_category_reliability_independent_of_global():
    r = SourceReliability()
    for _ in range(15):
        r.add("src", useful=True, category="good_lane")
    for _ in range(15):
        r.add("src", useful=False, category="bad_lane")
    good = r.reliability("src", category="good_lane")
    bad = r.reliability("src", category="bad_lane")
    assert good > bad


# --- trustworthiness (rho_trust) -------------------------------------------

def test_trust_unknown_is_exploratory():
    t = Trustworthiness(rho_unknown=0.75)
    assert t.trust("new") == 0.75


def test_unassessable_claim_is_ignored():
    t = Trustworthiness()
    t.add("src", ClaimQuality(well_formed=None))
    # no assessable evidence -> still exploratory, not penalized
    assert t.trust("src") == t.rho_unknown


def test_malformed_claims_reduce_trust_only():
    t = Trustworthiness(rho_unknown=0.75)
    for _ in range(20):
        t.add("spammer", ClaimQuality(well_formed=False))
    rho = t.trust("spammer")
    assert 0.25 <= rho < 0.75  # down-weighted, never below floor, never a boost


# --- trust_haircut safety shape --------------------------------------------

def test_haircut_never_unblocks():
    assert trust_haircut(1.0, "block", 1.0) == 0.0
    assert trust_haircut(1.0, "block_paper_setup", 0.9) == 0.0


def test_haircut_only_reduces_cleared_size():
    assert trust_haircut(1.0, "allow", 0.5) == pytest.approx(0.5)
    assert trust_haircut(1.0, "allow", 1.0) == pytest.approx(1.0)  # full trust = no cut
    assert trust_haircut(0.8, "allow", 0.5) == pytest.approx(0.4)


def test_haircut_clamps_rho():
    assert trust_haircut(1.0, "allow", 5.0) == pytest.approx(1.0)  # rho clamped to 1
    assert trust_haircut(1.0, "allow", -1.0) == 0.0  # rho clamped to 0


# --- market claim well-formedness (adapter) --------------------------------

def test_market_claim_none_when_no_levels():
    assert market_claim_well_formed(side="long", entry=100.0, stop=None, target=None) is None


def test_market_claim_none_when_no_entry():
    assert market_claim_well_formed(side="long", entry=None, stop=90.0, target=110.0) is None


def test_market_claim_sane_long():
    assert market_claim_well_formed(side="long", entry=100.0, stop=95.0, target=110.0) is True


def test_market_claim_bad_stop_side():
    # long with stop ABOVE entry is malformed
    assert market_claim_well_formed(side="long", entry=100.0, stop=105.0, target=110.0) is False


def test_market_claim_absurd_rr_rejected():
    # reward/risk of 1000:1 is implausible
    assert market_claim_well_formed(side="long", entry=100.0, stop=99.99, target=200.0) is False


def test_market_claim_feeds_trustworthiness():
    # the adapter output drives the neutral estimator via ClaimQuality
    t = Trustworthiness()
    wf = market_claim_well_formed(side="short", entry=100.0, stop=110.0, target=80.0)
    t.add("market_src", ClaimQuality(well_formed=wf))
    assert t.verdict("market_src").well_formed == 1.0
