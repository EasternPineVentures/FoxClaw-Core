#!/usr/bin/env python3
"""Sync read-only Forecast Desk snapshots into the local ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.adapters.event_contracts.kalshi import KalshiReadOnlyClient  # noqa: E402
from foxclaw.adapters.event_contracts.kalshi.models import payload_hash  # noqa: E402
from foxclaw.adapters.event_contracts.kalshi.normalize import (  # noqa: E402
    normalize_event,
    normalize_market,
    normalize_series,
)
from foxclaw.adapters.event_contracts.kalshi.orderbook import normalize_orderbook  # noqa: E402
from foxclaw.adapters.event_contracts.markets import to_jsonable  # noqa: E402
from foxclaw.adapters.event_contracts.storage.raw_archive import append_raw_response  # noqa: E402
from foxclaw.adapters.event_contracts.storage.repositories import ForecastRepository  # noqa: E402


class FixtureTransport:
    def __init__(self, fixture_dir: Path) -> None:
        self.fixture_dir = fixture_dir

    def get_json(self, path: str, params: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        clean = "/" + str(path).lstrip("/")
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
        raise KeyError(f"no fixture mapping for {path}")


def build_client(args: argparse.Namespace) -> KalshiReadOnlyClient:
    if args.fixture_dir:
        return KalshiReadOnlyClient(transport=FixtureTransport(Path(args.fixture_dir)))
    return KalshiReadOnlyClient(environment=args.environment)


def sync_once(args: argparse.Namespace) -> dict[str, Any]:
    client = build_client(args)
    repo = ForecastRepository(args.db)
    repo.init_db()
    raw_dir = args.raw_dir
    summary = {
        "mode": "PAPER",
        "credentials_loaded": False,
        "order_endpoint_invoked": False,
        "series": 0,
        "events": 0,
        "markets": 0,
        "orderbooks": 0,
        "db_path": str(repo.db_path),
    }

    series_items = client.list_series(category=args.category, limit=args.limit)
    for item in series_items:
        receipt = append_raw_response(raw_dir=raw_dir, endpoint="/series", payload=item, request={})
        repo.record_raw_payload(
            raw_hash=receipt.raw_hash,
            venue="kalshi",
            endpoint="/series",
            request={},
            response=item,
            archived_path=receipt.archive_path,
        )
        repo.record_series(normalize_series(item))
        summary["series"] += 1

    events = client.list_events(status=args.status, limit=args.limit, max_pages=args.max_pages)
    for item in events.items:
        receipt = append_raw_response(raw_dir=raw_dir, endpoint="/events", payload=item, request={})
        repo.record_raw_payload(
            raw_hash=receipt.raw_hash,
            venue="kalshi",
            endpoint="/events",
            request={},
            response=item,
            archived_path=receipt.archive_path,
        )
        repo.record_event(normalize_event(item))
        summary["events"] += 1
    repo.save_cursor("events", events.next_cursor)

    markets = client.list_markets(status=args.status, limit=args.limit, max_pages=args.max_pages)
    for item in markets.items:
        receipt = append_raw_response(raw_dir=raw_dir, endpoint="/markets", payload=item, request={})
        repo.record_raw_payload(
            raw_hash=receipt.raw_hash,
            venue="kalshi",
            endpoint="/markets",
            request={},
            response=item,
            archived_path=receipt.archive_path,
        )
        market = normalize_market(item)
        repo.record_market(market)
        summary["markets"] += 1

        raw_book = client.get_orderbook(market.market_id)
        book_receipt = append_raw_response(
            raw_dir=raw_dir,
            endpoint=f"/markets/{market.market_id}/orderbook",
            payload=raw_book,
            request={"ticker": market.market_id},
        )
        repo.record_raw_payload(
            raw_hash=book_receipt.raw_hash,
            venue="kalshi",
            endpoint="/markets/{ticker}/orderbook",
            request={"ticker": market.market_id},
            response=raw_book,
            archived_path=book_receipt.archive_path,
        )
        repo.record_orderbook(normalize_orderbook(raw_book, market_id=market.market_id))
        summary["orderbooks"] += 1
    repo.save_cursor("markets", markets.next_cursor)
    summary["counts"] = repo.counts()
    summary["raw_archive_hash"] = payload_hash({"counts": summary["counts"], "db_path": summary["db_path"]})
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", default="production", choices=("production", "demo"))
    parser.add_argument("--fixture-dir")
    parser.add_argument("--db")
    parser.add_argument("--raw-dir")
    parser.add_argument("--category")
    parser.add_argument("--status", default="open")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--once", action="store_true", help="run one sync pass")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.once:
        raise SystemExit("--once is required in Phase B; continuous sync belongs to a later phase")
    summary = sync_once(args)
    if args.json:
        print(json.dumps(to_jsonable(summary), indent=2, sort_keys=True))
    else:
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
