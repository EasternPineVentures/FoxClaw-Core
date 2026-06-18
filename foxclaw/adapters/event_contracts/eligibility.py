"""Eligibility gate for event-contract venues — always false for anything live.

This is the hard rail that makes the Forecast Desk an *intelligence* lane, not an execution
lane (invariant #1, called out for event contracts in invariant #11's corollary). No matter
the venue or jurisdiction, this gate returns: cannot submit orders, cannot move funds, live
execution not allowed, default authority ``A4_prohibited``. Going live is a separate,
founder-approved authority pass — never produced here, never a default.

Pure standard library. No I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Default authority for any execution-like action in the event-contract lane.
PROHIBITED_AUTHORITY: Final = "A4_prohibited"


@dataclass(frozen=True)
class Eligibility:
    """The verdict on what a caller may do at a venue. Live capability is structurally off."""

    venue: str
    jurisdiction: str | None
    can_submit_order: bool
    can_move_funds: bool
    live_allowed: bool
    authority_level: str
    reason: str


def assess_eligibility(venue: str, *, jurisdiction: str | None = None) -> Eligibility:
    """Return the eligibility verdict for ``venue``. Always read-only / paper-only.

    The signature accepts a jurisdiction so future, founder-approved, venue-and-jurisdiction-
    specific review can be layered *on top* — but the default and only behavior today is to
    deny every live capability. Read-only public data and paper simulation need no grant and
    are unaffected by this gate.
    """
    return Eligibility(
        venue=str(venue),
        jurisdiction=jurisdiction,
        can_submit_order=False,
        can_move_funds=False,
        live_allowed=False,
        authority_level=PROHIBITED_AUTHORITY,
        reason=(
            "read-only + paper-only; live execution is permanently gated behind a separate "
            "founder-approved authority pass (invariants #1, #11)"
        ),
    )
