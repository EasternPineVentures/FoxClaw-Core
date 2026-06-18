"""Cursor pagination helpers for Kalshi list endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .models import extract_items


@dataclass(frozen=True)
class PageReceipt:
    page_number: int
    request_cursor: str | None
    response_cursor: str | None
    item_count: int


@dataclass(frozen=True)
class PaginatedResult:
    items: tuple[Mapping[str, Any], ...]
    receipts: tuple[PageReceipt, ...]
    next_cursor: str | None
    stopped_reason: str


class PaginationError(RuntimeError):
    pass


def paginate(
    fetch_page: Callable[[dict[str, Any]], Mapping[str, Any]],
    *,
    collection_key: str,
    start_cursor: str | None = None,
    max_pages: int = 20,
    max_items: int = 1000,
) -> PaginatedResult:
    if max_pages <= 0:
        raise ValueError("max_pages must be positive")
    if max_items <= 0:
        raise ValueError("max_items must be positive")

    cursor = start_cursor or None
    seen_cursors: set[str] = set()
    receipts: list[PageReceipt] = []
    items: list[Mapping[str, Any]] = []

    for page_number in range(1, max_pages + 1):
        params: dict[str, Any] = {}
        if cursor:
            if cursor in seen_cursors:
                raise PaginationError(f"repeated request cursor {cursor!r}")
            seen_cursors.add(cursor)
            params["cursor"] = cursor
        page = fetch_page(params)
        page_items = extract_items(page, collection_key)
        next_cursor_raw = page.get("cursor")
        next_cursor = str(next_cursor_raw).strip() if next_cursor_raw not in (None, "") else None
        receipts.append(
            PageReceipt(
                page_number=page_number,
                request_cursor=cursor,
                response_cursor=next_cursor,
                item_count=len(page_items),
            )
        )
        remaining = max_items - len(items)
        items.extend(page_items[:remaining])
        if len(items) >= max_items:
            return PaginatedResult(tuple(items), tuple(receipts), next_cursor, "max_items")
        if next_cursor is None:
            return PaginatedResult(tuple(items), tuple(receipts), None, "cursor_exhausted")
        if next_cursor == cursor or next_cursor in seen_cursors:
            raise PaginationError(f"repeated response cursor {next_cursor!r}")
        cursor = next_cursor

    return PaginatedResult(tuple(items), tuple(receipts), cursor, "max_pages")
