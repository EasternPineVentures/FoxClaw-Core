from pathlib import Path

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


class FakeRepresentativeClient:
    def __init__(self) -> None:
        self.replies: list[tuple[str, str, str]] = []
        self.messages = {
            "chan_general": [
                {
                    "id": "200",
                    "content": "<@bot_1> what is CoinFox?",
                    "author": {"id": "user_1", "bot": False},
                    "mentions": [{"id": "bot_1"}],
                }
            ]
        }

    def channel_messages(self, channel_id: str, *, after: str | None = None, limit: int = 50):
        return list(self.messages.get(channel_id, []))

    def create_message(self, channel_id: str, content: str, *, message_reference: str):
        self.replies.append((channel_id, content, message_reference))
        return {"id": "reply_1", "content": content}


def test_run_once_dry_run_does_not_send_reply(tmp_path: Path) -> None:
    client = FakeRepresentativeClient()

    result = rep.run_once(
        client,
        bot_user_id="bot_1",
        channels={"chan_general": "general"},
        state_path=tmp_path / "state.json",
        send=False,
    )

    assert result["processed"] == 1
    assert result["would_reply"] == 1
    assert result["sent"] == 0
    assert client.replies == []


def test_run_once_send_posts_reply_and_updates_state(tmp_path: Path) -> None:
    client = FakeRepresentativeClient()
    state_path = tmp_path / "state.json"

    result = rep.run_once(
        client,
        bot_user_id="bot_1",
        channels={"chan_general": "general"},
        state_path=state_path,
        send=True,
    )

    assert result["sent"] == 1
    assert client.replies[0][0] == "chan_general"
    assert client.replies[0][2] == "200"
    assert rep.load_state(state_path)["chan_general"] == "200"


def test_default_state_path_is_outside_repo_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    path = rep.default_state_path()

    assert path == tmp_path / ".coinfox" / "discord_rep_state.json"


def test_parse_public_channels_requires_name_and_id(tmp_path: Path) -> None:
    config = tmp_path / "channels.json"
    config.write_text(
        '{"channels":[{"id":"chan_general","name":"general"},{"id":"chan_help","name":"help"}]}',
        encoding="utf-8",
    )

    assert rep.load_channel_config(config) == {
        "chan_general": "general",
        "chan_help": "help",
    }
