"""Unit tests for the event-contract Forecast Desk scaffold (pin P10).

Locks the doctrine in code (mispriced probability = FoxClaw prob − market-implied − costs) and
proves the hard rails: read-only / paper-only, live eligibility always false, no nonpublic
information posture (invariants #1, #11).
"""
from __future__ import annotations

import pytest

from foxclaw.adapters import event_contracts as ec
from foxclaw.adapters.event_contracts import eligibility, pricing, venues


# --- hard locks (invariants #1 + #11) ---------------------------------------

def test_lane_cannot_submit_or_move_funds():
    assert ec.CAN_SUBMIT_ORDER is False
    assert ec.CAN_MOVE_FUNDS is False
    assert ec.LIVE_EXECUTION_ALLOWED is False
    assert ec.USES_NONPUBLIC_INFORMATION is False
    assert ec.DEFAULT_AUTHORITY_LEVEL == "A4_prohibited"


def test_eligibility_is_always_read_only_paper_only():
    for venue, juris in [("kalshi", "US"), ("kalshi", None), ("anything", "elsewhere")]:
        e = eligibility.assess_eligibility(venue, jurisdiction=juris)
        assert e.can_submit_order is False
        assert e.can_move_funds is False
        assert e.live_allowed is False
        assert e.authority_level == "A4_prohibited"


# --- venues -----------------------------------------------------------------

def test_kalshi_is_the_first_venue_and_read_only():
    v = venues.get_venue("Kalshi")  # case-insensitive
    assert v.name == "Kalshi"
    assert v.read_only is True
    assert v.public_data_requires_auth is False
    assert "CFTC" in v.regulatory_status


def test_unknown_venue_raises_not_silently_tradeable():
    with pytest.raises(KeyError):
        venues.get_venue("polymarket")


# --- pricing: the doctrine in code ------------------------------------------

def test_yes_price_cents_to_implied_probability():
    assert pricing.yes_price_to_implied_probability(43) == pytest.approx(0.43)
    assert pricing.yes_price_to_implied_probability(98) == pytest.approx(0.98)


def test_no_price_is_complement():
    assert pricing.no_price_to_implied_probability(43) == pytest.approx(0.57)


@pytest.mark.parametrize("bad", [-1, 101, float("nan"), float("inf")])
def test_price_out_of_band_rejected(bad):
    with pytest.raises(ValueError):
        pricing.yes_price_to_implied_probability(bad)


def test_edge_gap_is_foxclaw_minus_market():
    assert pricing.edge_gap(foxclaw_probability=0.62, market_probability=0.43) == pytest.approx(0.19)


def test_usable_edge_subtracts_costs():
    # 0.62 - 0.43 = 0.19 gross; minus 2% fees = 0.17 usable, favoring YES.
    e = pricing.usable_edge(foxclaw_probability=0.62, market_probability=0.43, fees=0.02)
    assert e == pytest.approx(0.17)


def test_usable_edge_zero_when_costs_exceed_gap():
    e = pricing.usable_edge(foxclaw_probability=0.50, market_probability=0.47,
                            spread=0.02, fees=0.02)  # gap 0.03, costs 0.04
    assert e == 0.0


def test_usable_edge_is_signed_for_the_no_side():
    # FoxClaw less bullish than market -> edge favors NO -> negative usable edge.
    e = pricing.usable_edge(foxclaw_probability=0.30, market_probability=0.43, fees=0.01)
    assert e < 0
    assert pricing.favored_side(e) == "no"


def test_high_probability_event_priced_high_is_not_an_edge():
    # The doctrine: a 95% event at 98c is boring (market prices it ABOVE FoxClaw).
    e = pricing.usable_edge(foxclaw_probability=0.95, market_probability=0.98)
    assert e < 0  # favors NO if anything, certainly not a YES edge


def test_invalid_probability_rejected():
    with pytest.raises(ValueError):
        pricing.edge_gap(foxclaw_probability=1.5, market_probability=0.4)


def test_negative_cost_rejected():
    with pytest.raises(ValueError):
        pricing.usable_edge(foxclaw_probability=0.6, market_probability=0.4, fees=-0.01)
