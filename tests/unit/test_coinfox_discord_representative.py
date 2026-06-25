from foxclaw.adapters.discord import representative as rep


def test_representative_ignores_unmentioned_messages() -> None:
    message = {
        "id": "100",
        "content": "what is CoinFox?",
        "author": {"id": "user_1", "bot": False},
        "mentions": [],
    }

    decision = rep.classify_message(
        message,
        bot_user_id="bot_1",
        channel_name="general",
        allowed_channel_ids={"chan_general"},
        channel_id="chan_general",
    )

    assert decision.action == "ignore"
    assert decision.reason == "not_mentioned"
    assert decision.reply is None


def test_representative_refuses_financial_advice() -> None:
    message = {
        "id": "101",
        "content": "<@bot_1> should I buy BTC right now?",
        "author": {"id": "user_1", "bot": False},
        "mentions": [{"id": "bot_1"}],
    }

    decision = rep.classify_message(
        message,
        bot_user_id="bot_1",
        channel_name="trade-ideas",
        allowed_channel_ids={"chan_trade"},
        channel_id="chan_trade",
    )

    assert decision.action == "reply"
    assert decision.reason == "refuse_trade_advice"
    assert "cannot tell you what to trade" in decision.reply


def test_representative_routes_channel_questions() -> None:
    message = {
        "id": "102",
        "content": "<@bot_1> where do I post a setup idea?",
        "author": {"id": "user_1", "bot": False},
        "mentions": [{"id": "bot_1"}],
    }

    decision = rep.classify_message(
        message,
        bot_user_id="bot_1",
        channel_name="questions",
        allowed_channel_ids={"chan_questions"},
        channel_id="chan_questions",
    )

    assert decision.action == "reply"
    assert decision.reason == "route_trade_ideas"
    assert "#trade-ideas" in decision.reply
