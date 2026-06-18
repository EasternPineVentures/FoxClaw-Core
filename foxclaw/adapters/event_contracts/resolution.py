"""Final outcome / settlement evidence for a resolved market (stub — Phase 2).

Records how a market actually resolved, with the public settlement evidence — the ground
truth the forecast scoreboard scores against. Read-only; this observes outcomes, it never
settles or pays anything.

Stub: signatures + docstrings only. No live calls yet (pin P10, Phase 2).
"""

from __future__ import annotations

from typing import Any, Mapping


def record_resolution(market: Mapping[str, Any], outcome: str, evidence_url: str) -> dict[str, Any]:
    """Capture a market's resolved outcome (``yes`` / ``no`` / ``void``) + its public evidence.

    Target fields: ``market_id``, ``resolved_outcome``, ``resolved_at``, ``evidence_url``
    (public), ``settlement_note``.
    """
    raise NotImplementedError("resolution.record_resolution: Phase 2 of the Forecast Desk (P10)")
