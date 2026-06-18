#!/usr/bin/env python3
"""Read-only Kalshi API Desk.

Default operation is public REST only and credential-free. Tests pass a fixture
directory so the default suite stays deterministic and offline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw import __version__  # noqa: E402
from foxclaw.adapters import event_contracts as ec  # noqa: E402
from foxclaw.adapters.event_contracts.kalshi import KalshiReadOnlyClient, get_environment  # noqa: E402
from foxclaw.adapters.event_contracts.kalshi.normalize import (  # noqa: E402
    normalize_event,
    normalize_market,
    normalize_series,
)
from foxclaw.adapters.event_contracts.kalshi.orderbook import normalize_orderbook  # noqa: E402
from foxclaw.adapters.event_contracts.markets import to_jsonable  # noqa: E402


class FixtureTransport:
    """Tiny file-backed transport for regression tests and offline demos."""

    def __init__(self, fixture_dir: Path) -> None:
        self.fixture_dir = fixture_dir
        self.requests: list[tuple[str, dict[str, Any]]] = []

    def get_json(self, path: str, params: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        clean = "/" + str(path).lstrip("/")
        self.requests.append((clean, dict(params or {})))
        filename = self._filename(clean)
        loaded = json.loads((self.fixture_dir / filename).read_text(encoding="utf-8"))
        if not isinstance(loaded, Mapping):
            raise TypeError(f"fixture {filename} must contain a JSON object")
        return loaded

    @staticmethod
    def _filename(path: str) -> str:
        if path == "/series":
            return "series_page.json"
        if path == "/events":
            return "events_page.json"
        if path == "/markets":
            return "markets_page.json"
        if path == "/markets/trades":
            return "trades_page.json"
        if path.endswith("/orderbook"):
            return "orderbook.json"
        if path.startswith("/markets/"):
            return "market_detail.json"
        if path == "/historical/cutoff":
            return "historical_cutoff.json"
        if path == "/historical/markets":
            return "markets_page.json"
        if path.startswith("/historical/markets/"):
            return "historical_market.json"
        raise KeyError(f"no fixture mapping for {path}")


def build_client(args: argparse.Namespace) -> KalshiReadOnlyClient:
    if args.fixture_dir:
        return KalshiReadOnlyClient(transport=FixtureTransport(Path(args.fixture_dir)))
    return KalshiReadOnlyClient(environment=args.environment)


def print_payload(payload: Mapping[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def cmd_doctor(args: argparse.Namespace) -> int:
    env = get_environment(args.environment)
    payload = {
        "tool": "kalshi_api_desk",
        "foxclaw_version": __version__,
        "environment": env.name,
        "rest_base_url": env.rest_base_url,
        "public_rest_market_data_requires_auth": env.requires_credentials_for_rest_market_data,
        "credentials_loaded": False,
        "can_submit_order": ec.CAN_SUBMIT_ORDER,
        "can_move_funds": ec.CAN_MOVE_FUNDS,
        "live_execution_allowed": ec.LIVE_EXECUTION_ALLOWED,
        "authority_level": ec.DEFAULT_AUTHORITY_LEVEL,
        "fixture_mode": bool(args.fixture_dir),
        "network_called": False,
    }
    print_payload(payload, as_json=args.json)
    return 0


def cmd_series(args: argparse.Namespace) -> int:
    items = build_client(args).list_series(category=args.category, limit=args.limit)
    payload = {
        "series": [normalize_series(item) for item in items],
        "count": len(items),
    }
    print_payload(payload, as_json=args.json)
    return 0


def cmd_events(args: argparse.Namespace) -> int:
    result = build_client(args).list_events(status=args.status, limit=args.limit, max_pages=args.max_pages)
    payload = {
        "events": [normalize_event(item) for item in result.items],
        "count": len(result.items),
        "pagination": result,
    }
    print_payload(payload, as_json=args.json)
    return 0


def cmd_markets(args: argparse.Namespace) -> int:
    result = build_client(args).list_markets(status=args.status, limit=args.limit, max_pages=args.max_pages)
    payload = {
        "markets": [normalize_market(item) for item in result.items],
        "count": len(result.items),
        "pagination": result,
    }
    print_payload(payload, as_json=args.json)
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    market = build_client(args).get_market(args.ticker)
    payload = {"market": normalize_market(market), "raw_payload_hash": normalize_market(market).raw_payload_hash}
    print_payload(payload, as_json=args.json)
    return 0


def cmd_orderbook(args: argparse.Namespace) -> int:
    raw = build_client(args).get_orderbook(args.ticker)
    payload = {"orderbook": normalize_orderbook(raw, market_id=args.ticker)}
    print_payload(payload, as_json=args.json)
    return 0


def cmd_trades(args: argparse.Namespace) -> int:
    result = build_client(args).list_trades(ticker=args.ticker, limit=args.limit, max_pages=args.max_pages)
    payload = {
        "trades": result.items,
        "count": len(result.items),
        "pagination": result,
    }
    print_payload(payload, as_json=args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", default="production", choices=("production", "demo"))
    parser.add_argument("--fixture-dir", help="offline fixture directory for tests/demos")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("series")
    p.add_argument("--category")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_series)

    p = sub.add_parser("events")
    p.add_argument("--status")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--max-pages", type=int, default=5)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_events)

    p = sub.add_parser("markets")
    p.add_argument("--status")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--max-pages", type=int, default=5)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_markets)

    p = sub.add_parser("inspect")
    p.add_argument("--ticker", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("orderbook")
    p.add_argument("--ticker", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_orderbook)

    p = sub.add_parser("trades")
    p.add_argument("--ticker")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--max-pages", type=int, default=5)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_trades)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
