"""Event-contract venue metadata — Kalshi first.

Static, public, read-only descriptors of the venues the Forecast Desk may *read* (never
trade on). Kalshi is the first lane because it is the cleanest US regulated path (a
CFTC-designated contract market with public, no-auth market-data endpoints). Every other
venue stays ``read_only_public_data_only`` until a separate, founder-approved,
venue-and-jurisdiction-specific review is done (pin P10).

The space is described as *emerging, partially regulated, jurisdiction-sensitive* — never
"unregulated." This module is metadata, not legal advice.

Pure standard library. No I/O, no network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True)
class Venue:
    """A read-only descriptor for an event-contract venue."""

    name: str
    regulatory_status: str
    public_market_data_url: str
    public_data_requires_auth: bool
    # Posture flags — all venues are read-only/paper-only here (see eligibility.assess_eligibility).
    read_only: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)


VENUES: Final[dict[str, Venue]] = {
    "kalshi": Venue(
        name="Kalshi",
        regulatory_status="CFTC-designated contract market (emerging, jurisdiction-sensitive space)",
        public_market_data_url="https://api.elections.kalshi.com/trade-api/v2",
        public_data_requires_auth=False,
        notes=(
            "First US lane: cleanest regulated path.",
            "Public market data is reachable read-only without authentication.",
            "FoxClaw posture: read-only data + paper simulation only; no account, no funds.",
        ),
    ),
}


def get_venue(name: str) -> Venue:
    """Look up a venue descriptor by case-insensitive name. Raises ``KeyError`` if unknown —
    an unknown venue must never be silently treated as tradeable."""
    key = str(name or "").strip().lower()
    if key not in VENUES:
        raise KeyError(f"unknown event-contract venue: {name!r} (known: {sorted(VENUES)})")
    return VENUES[key]
