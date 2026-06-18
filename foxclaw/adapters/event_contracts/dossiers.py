"""Evidence + resolution-source dossiers for a market (stub — Phase 2).

A dossier is the public-evidence packet behind a FoxClaw probability estimate: what the
question really asks, how it resolves, and the lawfully-public sources that bear on it. This
is exactly where invariant #11 bites — every evidence item must be public; insider/hacked/
classified/private material is rejected at intake, never "used carefully."

Stub: signatures + docstrings only. No live calls yet (pin P10, Phase 2).
"""

from __future__ import annotations

from typing import Any, Mapping


def build_dossier(market: Mapping[str, Any], evidence: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Assemble a market's evidence dossier from public sources only.

    Must reject any evidence item that is not lawfully public (invariant #11). Target fields:
    ``market_id``, ``resolution_criteria``, ``resolution_source``, ``evidence`` (each with a
    public-source citation), ``foxclaw_probability``, ``rationale``.
    """
    raise NotImplementedError("dossiers.build_dossier: Phase 2 of the Forecast Desk (P10)")
