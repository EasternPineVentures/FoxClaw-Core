"""foxclaw.adapters.event_contracts — the Forecast Desk (Kalshi-first), pin P10.

A read-only + paper-only intelligence lane over event-contract markets, hunting *mispriced
probability* (see `docs/forecast_desk_plan.md`). Market/venue vocabulary lives here, never in
`engine/` (invariant #4); the lane reuses the neutral decision spine through the same adapter
border the market scoreboard uses.

HARD LOCKS (invariants #1 + #11) — structural, not optional. The whole package is wired so
the answer to "can this place an order or move money?" is **no**, by construction:
"""

from __future__ import annotations

from typing import Final

# These are read by callers/tests as the lane's posture. They are constants, not config —
# flipping them is a separate, founder-approved authority change, never a code default.
CAN_SUBMIT_ORDER: Final = False
CAN_MOVE_FUNDS: Final = False
LIVE_EXECUTION_ALLOWED: Final = False
USES_NONPUBLIC_INFORMATION: Final = False  # invariant #11 — public evidence only
DEFAULT_AUTHORITY_LEVEL: Final = "A4_prohibited"

from .eligibility import Eligibility, assess_eligibility  # noqa: E402
from .dossiers import assess_evidence_eligibility, build_dossier  # noqa: E402
from .policy import assess_event_contract_policy  # noqa: E402
from .pricing import (  # noqa: E402
    edge_gap,
    favored_side,
    no_price_to_implied_probability,
    usable_edge,
    yes_price_to_implied_probability,
)
from .resolution import assess_resolution_quality, record_resolution  # noqa: E402
from .scoring import assess_forecast  # noqa: E402
from .venues import VENUES, Venue, get_venue  # noqa: E402

__all__ = [
    # hard locks
    "CAN_SUBMIT_ORDER",
    "CAN_MOVE_FUNDS",
    "LIVE_EXECUTION_ALLOWED",
    "USES_NONPUBLIC_INFORMATION",
    "DEFAULT_AUTHORITY_LEVEL",
    # pricing (doctrine in code)
    "yes_price_to_implied_probability",
    "no_price_to_implied_probability",
    "edge_gap",
    "usable_edge",
    "favored_side",
    # eligibility (always read-only/paper-only)
    "assess_eligibility",
    "Eligibility",
    # dossiers / resolution / policy
    "assess_evidence_eligibility",
    "build_dossier",
    "assess_resolution_quality",
    "record_resolution",
    "assess_event_contract_policy",
    "assess_forecast",
    # venues
    "get_venue",
    "VENUES",
    "Venue",
]
