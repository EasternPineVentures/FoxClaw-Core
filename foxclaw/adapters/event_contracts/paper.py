"""Paper-only event-contract position receipts (stub — Phase 3).

Simulated entries/exits on event contracts, recorded as auditable receipts — the event-lane
analogue of `store/outcomes.py`'s paper positions. **Paper-only, always** (invariant #1): no
order ever leaves the building, no funds ever move. Every receipt carries
``can_submit_order=false`` / ``can_move_funds=false`` and authority ``A4_prohibited``.

Stub: signatures + docstrings only. No live calls yet (pin P10, Phase 3).
"""

from __future__ import annotations

from typing import Any, Mapping


def open_paper_position(market: Mapping[str, Any], side: str, stake: float) -> dict[str, Any]:
    """Open a SIMULATED event-contract position. Never a live order (invariant #1)."""
    raise NotImplementedError("paper.open_paper_position: Phase 3 of the Forecast Desk (P10)")


def close_paper_position(position: Mapping[str, Any], resolution: Mapping[str, Any]) -> dict[str, Any]:
    """Close a SIMULATED position against a recorded resolution, producing an outcome receipt."""
    raise NotImplementedError("paper.close_paper_position: Phase 3 of the Forecast Desk (P10)")
