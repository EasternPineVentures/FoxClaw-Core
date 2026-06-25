from foxclaw.adapters.discord import reset


class FakeResetClient:
    def __init__(self, *, include_public: bool = False, include_launch_channels: bool = False) -> None:
        self.fail_patch_ids: set[str] = set()
        self.channels: list[dict[str, object]] = [
            {
                "id": "cat_old",
                "name": "OLD",
                "type": reset.CHANNEL_TYPE_CATEGORY,
                "permission_overwrites": [],
            },
            {
                "id": "chan_old",
                "name": "old-chat",
                "type": reset.CHANNEL_TYPE_TEXT,
                "parent_id": "cat_old",
                "permission_overwrites": [],
            },
            {
                "id": "voice_old",
                "name": "old-stat",
                "type": 2,
                "parent_id": "cat_old",
                "permission_overwrites": [],
            },
            {
                "id": "chan_orphan",
                "name": "old-orphan",
                "type": reset.CHANNEL_TYPE_TEXT,
                "parent_id": None,
                "permission_overwrites": [],
            },
        ]
        if include_public:
            self.channels.extend(
                [
                    {
                        "id": "cat_public",
                        "name": "COINFOX",
                        "type": reset.CHANNEL_TYPE_CATEGORY,
                        "permission_overwrites": [],
                    },
                    {
                        "id": "chan_public",
                        "name": "general",
                        "type": reset.CHANNEL_TYPE_TEXT,
                        "parent_id": "cat_public",
                        "permission_overwrites": [],
                    },
                ]
            )
        if include_launch_channels:
            self.channels.extend(
                [
                    {
                        "id": "cat_start",
                        "name": "START HERE",
                        "type": reset.CHANNEL_TYPE_CATEGORY,
                        "permission_overwrites": [],
                    },
                    {
                        "id": "chan_welcome",
                        "name": "welcome",
                        "type": reset.CHANNEL_TYPE_TEXT,
                        "parent_id": "cat_start",
                        "permission_overwrites": [],
                    },
                    {
                        "id": "chan_rules",
                        "name": "rules",
                        "type": reset.CHANNEL_TYPE_TEXT,
                        "parent_id": "cat_start",
                        "permission_overwrites": [],
                    },
                    {
                        "id": "cat_coinfox",
                        "name": "COINFOX",
                        "type": reset.CHANNEL_TYPE_CATEGORY,
                        "permission_overwrites": [],
                    },
                    {
                        "id": "chan_trade_ideas",
                        "name": "trade-ideas",
                        "type": reset.CHANNEL_TYPE_TEXT,
                        "parent_id": "cat_coinfox",
                        "permission_overwrites": [],
                    },
                    {
                        "id": "cat_ideas",
                        "name": "FOXCLAW IDEAS",
                        "type": reset.CHANNEL_TYPE_CATEGORY,
                        "permission_overwrites": [],
                    },
                    {
                        "id": "chan_public_intelligence",
                        "name": "public-intelligence",
                        "type": reset.CHANNEL_TYPE_TEXT,
                        "parent_id": "cat_ideas",
                        "permission_overwrites": [],
                    },
                    {
                        "id": "cat_support",
                        "name": "SUPPORT",
                        "type": reset.CHANNEL_TYPE_CATEGORY,
                        "permission_overwrites": [],
                    },
                    {
                        "id": "chan_help",
                        "name": "help",
                        "type": reset.CHANNEL_TYPE_TEXT,
                        "parent_id": "cat_support",
                        "permission_overwrites": [],
                    },
                ]
            )
        self.invites = [{"code": "old-one"}, {"code": "old-two"}]
        self.created: list[dict[str, object]] = []
        self.patched: list[tuple[str, dict[str, object]]] = []
        self.guild_patches: list[tuple[str, dict[str, object]]] = []
        self.deleted_invites: list[str] = []
        self.messages: list[dict[str, object]] = []
        self.pinned_message_ids: list[str] = []
        self.existing_pins_by_channel: dict[str, list[dict[str, object]]] = {}

    def guild_channels(self, guild_id: str) -> list[dict[str, object]]:
        return list(self.channels)

    def create_guild_channel(self, guild_id: str, payload: dict[str, object]) -> dict[str, object]:
        created = {**payload, "id": f"new_{len(self.channels)}"}
        self.channels.append(created)
        self.created.append(created)
        return created

    def patch_channel(self, channel_id: str, payload: dict[str, object]) -> dict[str, object]:
        self.patched.append((channel_id, payload))
        if channel_id in self.fail_patch_ids:
            raise reset.DiscordAPIError("discord request failed: HTTP 403: Missing Permissions")
        for channel in self.channels:
            if channel.get("id") == channel_id:
                channel.update(payload)
                return channel
        raise AssertionError(f"unknown channel {channel_id}")

    def patch_guild(self, guild_id: str, payload: dict[str, object]) -> dict[str, object]:
        self.guild_patches.append((guild_id, payload))
        return {"id": guild_id, **payload}

    def guild_invites(self, guild_id: str) -> list[dict[str, object]]:
        return list(self.invites)

    def delete_invite(self, code: str) -> dict[str, object]:
        self.deleted_invites.append(code)
        return {"code": code}

    def channel_pins(self, channel_id: str) -> list[dict[str, object]]:
        return list(self.existing_pins_by_channel.get(channel_id, []))

    def create_message(self, channel_id: str, content: str) -> dict[str, object]:
        message = {"id": f"message_{len(self.messages)}", "channel_id": channel_id, "content": content}
        self.messages.append(message)
        return message

    def pin_message(self, channel_id: str, message_id: str) -> dict[str, object]:
        self.pinned_message_ids.append(message_id)
        return {"channel_id": channel_id, "message_id": message_id}


def test_revoke_all_invites_deletes_each_invite() -> None:
    client = FakeResetClient()

    result = reset.revoke_all_invites(client, "guild_1")

    assert result == {"revoked": ["old-one", "old-two"], "count": 2}
    assert client.deleted_invites == ["old-one", "old-two"]


def test_ensure_reset_structure_creates_private_and_public_layout() -> None:
    client = FakeResetClient()

    result = reset.ensure_reset_structure(client, "guild_1")

    created_names = [channel["name"] for channel in client.created]
    assert "FOUNDER VAULT" in created_names
    assert "RESET STAGING" in created_names
    assert "START HERE" in created_names
    assert "welcome" in created_names
    assert "foxclaw-postmortems" in created_names
    assert result["created_categories"] == [
        "FOUNDER VAULT",
        "RESET STAGING",
        "START HERE",
        "COINFOX",
        "FOXCLAW IDEAS",
        "LEARN",
        "SUPPORT",
    ]

    founder_vault = next(channel for channel in client.created if channel["name"] == "FOUNDER VAULT")
    assert founder_vault["permission_overwrites"] == [
        {
            "id": "guild_1",
            "type": reset.OVERWRITE_TYPE_ROLE,
            "allow": "0",
            "deny": str(reset.PERMISSION_VIEW_CHANNEL),
        }
    ]


def test_ensure_reset_structure_is_idempotent_for_existing_channels() -> None:
    client = FakeResetClient()
    reset.ensure_reset_structure(client, "guild_1")
    first_create_count = len(client.created)

    result = reset.ensure_reset_structure(client, "guild_1")

    assert result["created_categories"] == []
    assert result["created_channels"] == []
    assert len(client.created) == first_create_count


def test_permission_report_flags_missing_manage_channels() -> None:
    roles = [
        {"id": "guild_1", "name": "@everyone", "permissions": str(reset.PERMISSION_VIEW_CHANNEL)},
        {"id": "bot_role", "name": "CoinFox", "permissions": str(reset.PERMISSION_MANAGE_GUILD)},
    ]

    report = reset.permission_report(roles, ["bot_role"], "guild_1")

    assert report["has_manage_guild"] is True
    assert report["has_manage_channels"] is False
    assert report["missing"] == [
        "MANAGE_CHANNELS",
        "SEND_MESSAGES",
        "MANAGE_MESSAGES",
        "READ_MESSAGE_HISTORY",
    ]


def test_permission_report_flags_missing_posting_and_pin_permissions() -> None:
    roles = [
        {
            "id": "guild_1",
            "name": "@everyone",
            "permissions": str(reset.PERMISSION_MANAGE_CHANNELS | reset.PERMISSION_MANAGE_GUILD),
        }
    ]

    report = reset.permission_report(roles, [], "guild_1")

    assert report["has_send_messages"] is False
    assert report["has_manage_messages"] is False
    assert report["has_read_message_history"] is False
    assert report["missing"] == [
        "SEND_MESSAGES",
        "MANAGE_MESSAGES",
        "READ_MESSAGE_HISTORY",
    ]


def test_rename_guild_patches_server_name() -> None:
    client = FakeResetClient()

    result = reset.rename_guild(client, "guild_1", "CoinFox")

    assert result == {"guild_id": "guild_1", "name": "CoinFox"}
    assert client.guild_patches == [("guild_1", {"name": "CoinFox"})]


def test_hide_legacy_surface_hides_non_public_channels_only() -> None:
    client = FakeResetClient(include_public=True)

    result = reset.hide_legacy_surface(client, "guild_1")

    assert result["hidden_count"] == 4
    assert result["hidden"] == ["OLD", "old-chat", "old-stat", "old-orphan"]
    patched_ids = [channel_id for channel_id, _ in client.patched]
    assert patched_ids == ["cat_old", "chan_old", "voice_old", "chan_orphan"]
    assert "cat_public" not in patched_ids
    assert "chan_public" not in patched_ids
    for _, payload in client.patched:
        everyone = payload["permission_overwrites"][0]
        assert everyone["id"] == "guild_1"
        assert int(everyone["deny"]) & reset.PERMISSION_VIEW_CHANNEL


def test_hide_legacy_surface_records_channel_patch_failures_and_continues() -> None:
    client = FakeResetClient(include_public=True)
    client.fail_patch_ids = {"chan_old"}

    result = reset.hide_legacy_surface(client, "guild_1")

    assert result["hidden"] == ["OLD", "old-stat", "old-orphan"]
    assert result["failures"] == [
        {
            "channel": "old-chat",
            "channel_id": "chan_old",
            "error": "discord request failed: HTTP 403: Missing Permissions",
        }
    ]
    patched_ids = [channel_id for channel_id, _ in client.patched]
    assert patched_ids == ["cat_old", "chan_old", "voice_old", "chan_orphan"]


def test_seed_first_pinned_posts_posts_and_pins_launch_copy() -> None:
    client = FakeResetClient(include_launch_channels=True)

    result = reset.seed_first_pinned_posts(client, "guild_1")

    assert result["posted_count"] == 7
    assert result["skipped_count"] == 0
    assert result["missing_channels"] == []
    assert client.pinned_message_ids == [message["id"] for message in client.messages]
    messages_by_channel: dict[str, str] = {}
    for message in client.messages:
        channel_id = str(message["channel_id"])
        messages_by_channel[channel_id] = messages_by_channel.get(channel_id, "") + str(
            message["content"]
        )
    assert "**CoinFox Launch Note: Welcome**" in messages_by_channel["chan_welcome"]
    assert "**CoinFox Launch Note: Rules**" in messages_by_channel["chan_rules"]
    assert "**CoinFox Launch Note: Risk Disclaimer**" in messages_by_channel["chan_rules"]
    assert "**CoinFox Launch Note: Signals Are Not Trades**" in messages_by_channel[
        "chan_trade_ideas"
    ]
    assert "**CoinFox Launch Note: FoxClaw Public Intelligence**" in messages_by_channel[
        "chan_public_intelligence"
    ]
    assert "**CoinFox Launch Note: Help**" in messages_by_channel["chan_help"]


def test_seed_first_pinned_posts_skips_existing_markers() -> None:
    client = FakeResetClient(include_launch_channels=True)
    client.existing_pins_by_channel["chan_welcome"] = [
        {"id": "old_message", "content": "**CoinFox Launch Note: Welcome**\nAlready pinned."}
    ]

    result = reset.seed_first_pinned_posts(client, "guild_1")

    assert result["posted_count"] == 6
    assert result["skipped"] == [{"channel": "welcome", "marker": "CoinFox Launch Note: Welcome"}]
    assert all(message["channel_id"] != "chan_welcome" for message in client.messages)
