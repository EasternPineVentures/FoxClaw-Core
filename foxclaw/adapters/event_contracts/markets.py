"""Read-only market catalog normalization (stub — Phase 1).

Turns a venue's raw market listing (fetched elsewhere from *public* data) into a neutral
market record the rest of the desk can reason over. No network call lives here — a caller
hands in already-fetched public data; this only normalizes shape (invariant #11: public data
only). Read-only; nothing here can create, submit, or fund anything.

Stub: signatures + docstrings only. No live calls yet (pin P10, Phase 1).
"""

from __future__ import annotations

from typing import Any, Mapping


def normalize_market(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one venue-raw market dict into a neutral market record.

    Target neutral fields (to be finalized in Phase 1): ``venue``, ``market_id``, ``title``,
    ``yes_price_cents``, ``no_price_cents``, ``status``, ``close_time``, ``resolution_source``.
    """
    raise NotImplementedError("markets.normalize_market: Phase 1 of the Forecast Desk (P10)")
