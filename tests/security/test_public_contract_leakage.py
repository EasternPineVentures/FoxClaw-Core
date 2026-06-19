from __future__ import annotations

import json
from pathlib import Path

from foxclaw.policy.publication import DERIVATIVE_PUBLIC_SAFE, evaluate_publication

REPO = Path(__file__).resolve().parents[2]
PUBLIC_FIXTURE_DIR = REPO / "tests" / "fixtures" / "public_contract"

FORBIDDEN_PUBLIC_FRAGMENTS = (
    "private_source_ref",
    "raw_discord_quote",
    "discord.com/channels",
    "discord.gg/",
    "guild_id",
    "channel_id",
    "user_id",
    "api_key",
    "token=",
    "secret=",
)


def _walk_strings(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)
    elif isinstance(value, str):
        yield value


def test_public_contract_fixtures_do_not_contain_private_source_fragments():
    for path in PUBLIC_FIXTURE_DIR.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        blob = "\n".join(_walk_strings(payload)).lower()
        for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
            assert fragment not in blob, f"{path.name} leaked {fragment}"


def test_publication_gate_rejects_private_discord_payload_before_export():
    payload = {
        "publication_class": DERIVATIVE_PUBLIC_SAFE,
        "claim": "BTC looks strong. See https://discord.com/channels/123/456/789",
        "source_classification": "private",
        "verification_status": "verified",
        "presentation": "qualified",
        "contains_private_source_content": True,
    }
    result = evaluate_publication(payload)
    assert result.allowed is False
    assert result.contains_private_source_content is True
    assert "private_message_link" in result.reason_codes
    assert "contains_private_source_content" in result.reason_codes
