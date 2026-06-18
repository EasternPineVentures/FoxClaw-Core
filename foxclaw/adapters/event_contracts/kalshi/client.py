"""Typed read-only facade over Kalshi public REST market data."""

from __future__ import annotations

from typing import Any, Mapping

from .environments import KalshiEnvironment
from .historical import HistoricalCutoff, parse_historical_cutoff
from .orderbook import normalize_orderbook
from .pagination import PaginatedResult, paginate
from .transport import KalshiHttpClient


class KalshiReadOnlyClient:
    """A no-credentials client for public market-data discovery."""

    def __init__(
        self,
        *,
        environment: str | KalshiEnvironment = "production",
        transport: KalshiHttpClient | None = None,
    ) -> None:
        self.transport = transport or KalshiHttpClient(environment=environment)

    def list_series(self, *, category: str | None = None, limit: int | None = None) -> tuple[Mapping[str, Any], ...]:
        params: dict[str, Any] = {}
        if category:
            params["category"] = category
        payload = self.transport.get_json("/series", params)
        items = tuple(payload.get("series") or ())
        return items[:limit] if limit else items

    def list_events(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
        max_pages: int = 20,
        start_cursor: str | None = None,
    ) -> PaginatedResult:
        params: dict[str, Any] = {"limit": min(limit, 1000)}
        if status:
            params["status"] = status
        return self._paginated("/events", "events", params, limit, max_pages, start_cursor)

    def list_markets(
        self,
        *,
        status: str | None = None,
        series_ticker: str | None = None,
        event_ticker: str | None = None,
        tickers: str | None = None,
        limit: int = 100,
        max_pages: int = 20,
        start_cursor: str | None = None,
    ) -> PaginatedResult:
        params: dict[str, Any] = {"limit": min(limit, 1000)}
        for key, value in (
            ("status", status),
            ("series_ticker", series_ticker),
            ("event_ticker", event_ticker),
            ("tickers", tickers),
        ):
            if value:
                params[key] = value
        return self._paginated("/markets", "markets", params, limit, max_pages, start_cursor)

    def get_market(self, ticker: str) -> Mapping[str, Any]:
        payload = self.transport.get_json(f"/markets/{ticker}", {})
        market = payload.get("market", payload)
        if not isinstance(market, Mapping):
            raise TypeError("market response must contain an object")
        return market

    def get_orderbook(self, ticker: str) -> Mapping[str, Any]:
        return self.transport.get_json(f"/markets/{ticker}/orderbook", {})

    def normalized_orderbook(self, ticker: str):
        return normalize_orderbook(self.get_orderbook(ticker), market_id=ticker)

    def list_trades(
        self,
        *,
        ticker: str | None = None,
        limit: int = 100,
        max_pages: int = 20,
        start_cursor: str | None = None,
    ) -> PaginatedResult:
        params: dict[str, Any] = {"limit": min(limit, 1000)}
        if ticker:
            params["ticker"] = ticker
        return self._paginated("/markets/trades", "trades", params, limit, max_pages, start_cursor)

    def historical_cutoff(self) -> HistoricalCutoff:
        return parse_historical_cutoff(self.transport.get_json("/historical/cutoff", {}))

    def list_historical_markets(
        self,
        *,
        tickers: str | None = None,
        event_ticker: str | None = None,
        series_ticker: str | None = None,
        limit: int = 100,
        max_pages: int = 20,
        start_cursor: str | None = None,
    ) -> PaginatedResult:
        params: dict[str, Any] = {"limit": min(limit, 1000)}
        for key, value in (
            ("tickers", tickers),
            ("event_ticker", event_ticker),
            ("series_ticker", series_ticker),
        ):
            if value:
                params[key] = value
        return self._paginated("/historical/markets", "markets", params, limit, max_pages, start_cursor)

    def get_historical_market(self, ticker: str) -> Mapping[str, Any]:
        payload = self.transport.get_json(f"/historical/markets/{ticker}", {})
        market = payload.get("market", payload)
        if not isinstance(market, Mapping):
            raise TypeError("historical market response must contain an object")
        return market

    def _paginated(
        self,
        path: str,
        collection_key: str,
        base_params: dict[str, Any],
        limit: int,
        max_pages: int,
        start_cursor: str | None,
    ) -> PaginatedResult:
        def fetch_page(cursor_params: dict[str, Any]) -> Mapping[str, Any]:
            params = dict(base_params)
            params.update(cursor_params)
            return self.transport.get_json(path, params)

        return paginate(
            fetch_page,
            collection_key=collection_key,
            start_cursor=start_cursor,
            max_pages=max_pages,
            max_items=limit,
        )
