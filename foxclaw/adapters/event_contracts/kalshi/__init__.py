"""Kalshi read-only adapter for the Forecast Desk."""

from __future__ import annotations

from .client import KalshiReadOnlyClient
from .environments import KALSHI_ENVIRONMENTS, KalshiEnvironment, get_environment

__all__ = [
    "KalshiReadOnlyClient",
    "KALSHI_ENVIRONMENTS",
    "KalshiEnvironment",
    "get_environment",
]
