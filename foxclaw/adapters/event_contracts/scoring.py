"""Forecast scoreboard for the event-contract lane (stub — Phase 4).

The event-lane analogue of `adapters/market/scoreboard.py`: aggregate resolved paper
forecasts into win-rate / profit-factor / **edge-accuracy** (was FoxClaw's probability
actually calibrated?), per category, so the desk learns which categories it is good at. Like
the market scoreboard, the *grading* defers to the neutral `engine/` (score/gate); this module
only does the market/venue-specific reading and aggregation.

Stub: signatures + docstrings only. No live calls yet (pin P10, Phase 4).
"""

from __future__ import annotations

from typing import Any


def build_forecast_scoreboard(event_outcomes: list[Any]) -> dict[str, Any]:
    """Build the per-category forecast scoreboard from resolved paper event outcomes.

    Target metrics: win_rate, profit_factor, edge_accuracy (calibration), per category; graded
    onto the shared decision tiers via ``engine.score`` (reuse, don't re-implement).
    """
    raise NotImplementedError("scoring.build_forecast_scoreboard: Phase 4 of the Forecast Desk (P10)")
