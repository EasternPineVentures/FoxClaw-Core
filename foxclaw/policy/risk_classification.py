"""Shared risk vocabulary for public readiness and publication policy."""
from __future__ import annotations

RISK_RESEARCH = "RESEARCH"
RISK_WATCH = "WATCH"
RISK_STRUCTURED = "STRUCTURED"
RISK_TACTICAL = "TACTICAL"
RISK_SPECULATIVE = "SPECULATIVE"
RISK_REDLINE = "REDLINE"
RISK_REJECT = "REJECT"

RISK_CLASSES = (
    RISK_RESEARCH,
    RISK_WATCH,
    RISK_STRUCTURED,
    RISK_TACTICAL,
    RISK_SPECULATIVE,
    RISK_REDLINE,
    RISK_REJECT,
)

_ALIASES = {value.lower(): value for value in RISK_CLASSES}
_ALIASES.update({value.title().lower(): value for value in RISK_CLASSES})


def normalize_risk_class(value: str) -> str:
    """Normalize a risk class, failing closed to REJECT when unknown."""
    key = str(value or "").strip().replace("-", "_").replace(" ", "_").lower()
    return _ALIASES.get(key, RISK_REJECT)


def beginner_safe(risk_class: str) -> bool:
    """Return whether a risk class can be shown as beginner-safe."""
    return normalize_risk_class(risk_class) in {RISK_RESEARCH, RISK_WATCH, RISK_STRUCTURED}
