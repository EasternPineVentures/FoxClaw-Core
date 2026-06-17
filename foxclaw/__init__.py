"""FoxClaw — a receipt-driven, domain-neutral decision engine.

FoxClaw watches incoming source claims, scores them against an auditable track
record, sizes commitment under uncertainty, and records every step as a receipt.
It has a market adapter, but the core is domain-neutral by design.

Layering (dependencies point inward only):
    adapters/ -> engine/ -> store/ + policy/
The public airlock is `foxclaw.contract`; nothing outside it is part of the
public surface.
"""
from __future__ import annotations

from pathlib import Path

__all__ = ["__version__"]


def _read_version() -> str:
    """Single source of truth: the repo-root VERSION file (shown in FC titles)."""
    try:
        return (Path(__file__).resolve().parent.parent / "VERSION").read_text(
            encoding="utf-8"
        ).strip()
    except Exception:
        return "0.0.0"


__version__ = _read_version()
