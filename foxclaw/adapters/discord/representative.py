"""Mention-only CoinFox Discord representative bot helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
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


def load_state(path: str | Path) -> dict[str, str]:
    state_path = Path(path)
    if not state_path.exists():
        return {}
    return {
        str(key): str(value)
        for key, value in json.loads(state_path.read_text(encoding="utf-8")).items()
    }


def save_state(path: str | Path, state: dict[str, str]) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_once(
    client: Any,
    *,
    bot_user_id: str,
    channels: dict[str, str],
    state_path: str | Path,
    send: bool = False,
) -> dict[str, int]:
    state = load_state(state_path)
    summary = {"processed": 0, "would_reply": 0, "sent": 0, "ignored": 0}
    allowed_channel_ids = set(channels)
    for channel_id, channel_name in channels.items():
        after = state.get(channel_id)
        messages = client.channel_messages(channel_id, after=after, limit=50)
        for message in sorted(messages, key=lambda item: int(str(item.get("id") or "0"))):
            message_id = str(message.get("id") or "")
            if not message_id:
                continue
            decision = classify_message(
                message,
                bot_user_id=bot_user_id,
                channel_name=channel_name,
                allowed_channel_ids=allowed_channel_ids,
                channel_id=channel_id,
            )
            summary["processed"] += 1
            if decision.action == "reply" and decision.reply:
                summary["would_reply"] += 1
                if send:
                    client.create_message(channel_id, decision.reply, message_reference=message_id)
                    summary["sent"] += 1
            else:
                summary["ignored"] += 1
            state[channel_id] = message_id
    save_state(state_path, state)
    return summary


def _mentions_bot(message: dict[str, Any], bot_user_id: str) -> bool:
    return any(str(mention.get("id") or "") == bot_user_id for mention in message.get("mentions") or [])


def _contains_any(content: str, terms: tuple[str, ...]) -> bool:
    return any(term in content for term in terms)
