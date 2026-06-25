from foxclaw.adapters.discord import reset


class FakeResetClient:
    def __init__(self) -> None:
        self.channels: list[dict[str, object]] = [
            {
                "id": "cat_old",
                "name": "OLD",
                "type": reset.CHANNEL_TYPE_CATEGORY,
                "permission_overwrites": [],
            }
        ]
        self.invites = [{"code": "old-one"}, {"code": "old-two"}]
        self.created: list[dict[str, object]] = []
        self.patched: list[tuple[str, dict[str, object]]] = []
        self.deleted_invites: list[str] = []

    def guild_channels(self, guild_id: str) -> list[dict[str, object]]:
        return list(self.channels)

    def create_guild_channel(self, guild_id: str, payload: dict[str, object]) -> dict[str, object]:
        created = {**payload, "id": f"new_{len(self.channels)}"}
        self.channels.append(created)
        self.created.append(created)
        return created

    def patch_channel(self, channel_id: str, payload: dict[str, object]) -> dict[str, object]:
        self.patched.append((channel_id, payload))
        for channel in self.channels:
            if channel.get("id") == channel_id:
                channel.update(payload)
                return channel
        raise AssertionError(f"unknown channel {channel_id}")

    def guild_invites(self, guild_id: str) -> list[dict[str, object]]:
        return list(self.invites)

    def delete_invite(self, code: str) -> dict[str, object]:
        self.deleted_invites.append(code)
        return {"code": code}


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
    assert report["missing"] == ["MANAGE_CHANNELS"]

