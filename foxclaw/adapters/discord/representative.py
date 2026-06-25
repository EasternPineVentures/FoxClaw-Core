"""Mention-only CoinFox Discord representative bot helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RepresentativeDecision:
    action: str
    reason: str
    reply: str | None = None


TRADE_ADVICE_TERMS = (
    "should i buy",
    "should i sell",
    "buy now",
    "sell now",
    "enter",
    "exit",
    "leverage",
    "position size",
)

PRIVATE_HISTORY_TERMS = (
    "founder vault",
    "reset staging",
    "archive",
    "old signals",
    "private history",
    "bot log",
    "parser log",
)

CHANNEL_ROUTE_TERMS = ("where do i post", "setup idea", "trade idea", "which channel")

IDENTITY_REPLY = (
    "I am the CoinFox bot. I can explain the server, route questions, and keep "
    "the risk line clear. I cannot give financial advice or tell anyone what to trade."
)

TRADE_ADVICE_REFUSAL = (
    "I cannot tell you what to trade. I can help frame the idea, risk, "
    "invalidation, and where to discuss it. For setups, use #trade-ideas and "
    "label uncertainty clearly."
)

PRIVATE_HISTORY_REFUSAL = (
    "I cannot discuss private archives, Founder Vault, Reset Staging, or old "
    "server history. I can help with the public CoinFox channels and public-safe "
    "rules."
)

TRADE_IDEAS_ROUTE = (
    "Use #trade-ideas for structured setups. Include the idea, timeframe, risk, "
    "invalidation point, and what would change your mind."
)


def classify_message(
    message: dict[str, Any],
    *,
    bot_user_id: str,
    channel_name: str,
    allowed_channel_ids: set[str],
    channel_id: str,
) -> RepresentativeDecision:
    if channel_id not in allowed_channel_ids:
        return RepresentativeDecision("ignore", "channel_not_allowed")
    author = message.get("author") if isinstance(message.get("author"), dict) else {}
    if author.get("bot"):
        return RepresentativeDecision("ignore", "bot_author")
    if not _mentions_bot(message, bot_user_id):
        return RepresentativeDecision("ignore", "not_mentioned")

    content = str(message.get("content") or "").lower()
    if _contains_any(content, PRIVATE_HISTORY_TERMS):
        return RepresentativeDecision("reply", "refuse_private_history", PRIVATE_HISTORY_REFUSAL)
    if _contains_any(content, TRADE_ADVICE_TERMS):
        return RepresentativeDecision("reply", "refuse_trade_advice", TRADE_ADVICE_REFUSAL)
    if _contains_any(content, CHANNEL_ROUTE_TERMS):
        return RepresentativeDecision("reply", "route_trade_ideas", TRADE_IDEAS_ROUTE)
    return RepresentativeDecision("reply", "identity", IDENTITY_REPLY)


def _mentions_bot(message: dict[str, Any], bot_user_id: str) -> bool:
    return any(str(mention.get("id") or "") == bot_user_id for mention in message.get("mentions") or [])


def _contains_any(content: str, terms: tuple[str, ...]) -> bool:
    return any(term in content for term in terms)
