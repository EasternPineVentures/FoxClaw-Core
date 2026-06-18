from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from foxclaw.adapters.event_contracts.kalshi.orderbook import normalize_orderbook

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "kalshi"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_orderbook_combines_duplicate_levels_and_infers_asks():
    book = normalize_orderbook(_load("orderbook.json"), market_id="KXJOBLESS-26JUN18-T250")
    assert book.best_yes_bid == Decimal("0.4200")
    assert book.best_no_bid == Decimal("0.5700")
    assert book.best_yes_ask == Decimal("0.4300")
    assert book.best_no_ask == Decimal("0.5800")
    assert book.yes_spread == Decimal("0.0100")
    assert book.no_spread == Decimal("0.0100")
    assert book.depth_yes_at_best == Decimal("13.00")
    assert book.is_tradeable is True


def test_orderbook_handles_one_sided_book_without_inventing_ask():
    raw = {"orderbook_fp": {"yes_dollars": [["0.2500", "1.00"]], "no_dollars": []}}
    book = normalize_orderbook(raw, market_id="KXONE")
    assert book.best_yes_bid == Decimal("0.2500")
    assert book.best_yes_ask is None
    assert book.best_no_ask == Decimal("0.7500")
    assert book.is_tradeable is True


def test_orderbook_marks_crossed_book_invalid_not_tradeable():
    raw = {
        "orderbook_fp": {
            "yes_dollars": [["0.7000", "1.00"]],
            "no_dollars": [["0.4000", "1.00"]]
        }
    }
    book = normalize_orderbook(raw, market_id="KXCROSSED")
    assert book.is_tradeable is False
    assert "crossed_yes_book" in (book.invalid_reason or "")


def test_orderbook_rejects_float_fixed_point_values():
    raw = {"orderbook_fp": {"yes_dollars": [[0.42, "1.00"]], "no_dollars": []}}
    with pytest.raises(TypeError):
        normalize_orderbook(raw, market_id="KXBROKEN")
