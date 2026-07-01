from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.coinfox_packet_demo import evaluate_coinfox_packet_intake

REPO = Path(__file__).resolve().parents[2]
SOAK_DIR = REPO / "tests" / "fixtures" / "coinfox_packet_soak"
TOOL = REPO / "tools" / "coinfox_packet_demo.py"

EXPECTED_LABELS = {
    "official_sec_clean.allowed.json": "trusted_provenance",
    "official_sec_prompt_injection.blocked.json": "prompt_injection_blocked",
    "fred_clean.allowed.json": "trusted_provenance",
    "reddit_single_source_hype.quarantined.json": "unverified_social_heat",
    "reddit_two_corroborations.allowed.json": "unverified_social_heat",
    "reddit_duplicate_hype.quarantined.json": "unverified_social_heat",
    "discord_rumor.quarantined.json": "unverified_social_heat",
    "unknown_blog.quarantined.json": "new_source_needs_corroboration",
    "unknown_clean_two_corroborations.allowed.json": "new_source_corroborated",
    "news_watch_clean.quarantined_or_watch.json": "watch_source_needs_corroboration",
    "coindesk_watch_with_corroboration.allowed.json": "watch_source_corroborated",
    "kalshi_odds_move_watch.quarantined_or_watch.json": "odds_move_watch",
    "polymarket_odds_move_with_corroboration.allowed.json": "odds_move_watch",
    "raw_private_text_attempt.blocked.json": "private_text_blocked",
}

FORBIDDEN_METADATA_KEYS = {
    "confidence",
    "confidence_label",
    "confidence_score",
    "score",
    "source_score",
    "source_id",
    "source_name",
    "source_url",
    "raw_text",
    "content",
    "summary",
    "public_safe_summary",
}


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads((SOAK_DIR / name).read_text(encoding="utf-8"))


def _first_metadata(name: str) -> dict[str, Any]:
    evaluated = evaluate_coinfox_packet_intake(_load_fixture(name))
    metadata = evaluated["trust_metadata"]
    assert len(metadata) == 1
    return metadata[0]


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _assert_output_hides_observation(output: str, payload: dict[str, Any]) -> None:
    observation = payload["observation"]
    source = observation["source"]
    hidden_fragments = [
        observation.get("content", ""),
        observation.get("summary", ""),
        observation.get("public_safe_summary", ""),
        observation.get("observation_id", ""),
        source.get("source_id", ""),
        source.get("source_name", ""),
        source.get("source_url", ""),
    ]
    haystack = output.lower()
    for fragment in hidden_fragments:
        if fragment:
            assert fragment.lower() not in haystack


def test_packet_trust_metadata_v0_labels_full_soak_matrix():
    assert {path.name for path in SOAK_DIR.glob("*.json")} == set(EXPECTED_LABELS)

    for name, expected_label in EXPECTED_LABELS.items():
        metadata = _first_metadata(name)

        assert metadata["schema_version"] == "packet_trust_metadata.v0"
        assert metadata["label"] == expected_label
        assert metadata["display"]["display_label"]
        assert metadata["display"]["public_note"]
        assert metadata["display"]["operator_note"]


def test_packet_trust_metadata_v0_has_no_authority_or_scores():
    for name in EXPECTED_LABELS:
        metadata = _first_metadata(name)
        authority = metadata["authority"]

        assert authority
        assert all(value is False for value in authority.values())
        assert not (set(_walk_keys(metadata)) & FORBIDDEN_METADATA_KEYS)


def test_packet_trust_metadata_v0_json_sidecar_is_public_safe_for_allowed_unknown_source():
    fixture = SOAK_DIR / "unknown_clean_two_corroborations.allowed.json"
    payload = _load_fixture(fixture.name)
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--fixture",
            "--intake",
            str(fixture),
            "--json",
            "--trust-metadata",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    output = json.loads(completed.stdout)

    assert output["packet"]["schema_version"] == "coinfox_curated_packet.v1"
    assert output["trust_metadata"][0]["label"] == "new_source_corroborated"
    _assert_output_hides_observation(completed.stdout, payload)


def test_packet_trust_metadata_v0_markdown_sidecar_is_public_safe_for_allowed_unknown_source():
    fixture = SOAK_DIR / "unknown_clean_two_corroborations.allowed.json"
    payload = _load_fixture(fixture.name)
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--intake", str(fixture), "--trust-metadata"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "# CoinFox Curated Packet" in completed.stdout
    assert "## Packet Trust Metadata V0" in completed.stdout
    assert "new_source_corroborated" in completed.stdout
    _assert_output_hides_observation(completed.stdout, payload)


def test_packet_trust_metadata_v0_blocked_output_stays_sanitized_when_requested():
    fixture = SOAK_DIR / "official_sec_prompt_injection.blocked.json"
    payload = _load_fixture(fixture.name)
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--intake", str(fixture), "--trust-metadata"],
        cwd=REPO,
        text=True,
        capture_output=True,
    )
    output = json.loads(completed.stdout)

    assert completed.returncode == 2
    assert output["error"] == "quarantined"
    assert output["reason"] == "PROMPT_INJECTION_FLAGGED"
    assert output["trust_metadata"][0]["label"] == "prompt_injection_blocked"
    _assert_output_hides_observation(completed.stdout, payload)
