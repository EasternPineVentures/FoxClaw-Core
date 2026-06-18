from __future__ import annotations

import pytest

from foxclaw.adapters.event_contracts.kalshi.pagination import PaginationError, paginate


def test_pagination_follows_cursor_until_exhausted():
    pages = {
        None: {"markets": [{"ticker": "A"}], "cursor": "next"},
        "next": {"markets": [{"ticker": "B"}], "cursor": None},
    }

    def fetch(params):
        return pages[params.get("cursor")]

    result = paginate(fetch, collection_key="markets", max_pages=5, max_items=10)
    assert [item["ticker"] for item in result.items] == ["A", "B"]
    assert [r.request_cursor for r in result.receipts] == [None, "next"]
    assert result.stopped_reason == "cursor_exhausted"


def test_pagination_stops_at_max_items_with_resume_cursor():
    pages = {None: {"markets": [{"ticker": "A"}, {"ticker": "B"}], "cursor": "next"}}

    result = paginate(lambda params: pages[params.get("cursor")], collection_key="markets", max_items=1)
    assert [item["ticker"] for item in result.items] == ["A"]
    assert result.next_cursor == "next"
    assert result.stopped_reason == "max_items"


def test_pagination_rejects_repeated_response_cursor():
    def fetch(params):
        return {"markets": [{"ticker": "A"}], "cursor": "again"}

    with pytest.raises(PaginationError):
        paginate(fetch, collection_key="markets", max_pages=3, max_items=10)
