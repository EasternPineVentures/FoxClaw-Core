"""Kalshi REST/WebSocket environment descriptors.

Phase A uses REST only. WebSocket URLs are named here so the boundary is explicit, but
no WebSocket connection is opened in the read-only API Desk.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class KalshiEnvironment:
    name: str
    rest_base_url: str
    websocket_url: str
    requires_credentials_for_rest_market_data: bool
    credentials_namespace: str


KALSHI_ENVIRONMENTS: Final[dict[str, KalshiEnvironment]] = {
    "production": KalshiEnvironment(
        name="production",
        rest_base_url="https://external-api.kalshi.com/trade-api/v2",
        websocket_url="wss://external-api-ws.kalshi.com/trade-api/ws/v2",
        requires_credentials_for_rest_market_data=False,
        credentials_namespace="KALSHI_PRODUCTION",
    ),
    "demo": KalshiEnvironment(
        name="demo",
        rest_base_url="https://external-api.demo.kalshi.co/trade-api/v2",
        websocket_url="wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2",
        requires_credentials_for_rest_market_data=False,
        credentials_namespace="KALSHI_DEMO",
    ),
}


def get_environment(name: str = "production") -> KalshiEnvironment:
    key = str(name or "production").strip().lower()
    if key not in KALSHI_ENVIRONMENTS:
        raise KeyError(f"unknown Kalshi environment: {name!r}")
    return KALSHI_ENVIRONMENTS[key]
