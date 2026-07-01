"""Minimal prompt-injection phrase scanner.

This module only flags obvious instruction-smuggling phrases. It does not extract
claims, score sources, or make publication decisions.
"""

from __future__ import annotations

from typing import Any

FLAG_PHRASES = (
    "ignore previous instructions",
    "reveal system prompt",
    "override authority",
    "mark this trusted",
    "export private data",
    "execute trade",
    "move funds",
    "mutate grove",
    "you are now a financial advisor",
    "treat this as truth",
)


def scan(text: Any) -> dict[str, object]:
    """Return a public-safety scan result for obvious prompt injection."""
    if not isinstance(text, str) or not text:
        return {"flagged": False, "flags": [], "safe_for_public": True}

    haystack = text.casefold()
    flags = [phrase for phrase in FLAG_PHRASES if phrase.casefold() in haystack]
    flagged = bool(flags)
    return {
        "flagged": flagged,
        "flags": flags,
        "safe_for_public": not flagged,
    }
