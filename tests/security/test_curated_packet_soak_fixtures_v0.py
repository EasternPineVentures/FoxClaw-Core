from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SOAK_DIR = REPO / "tests" / "fixtures" / "coinfox_packet_soak"
SOAK_FIXTURE = SOAK_DIR / "unknown_clean_two_corroborations.allowed.json"
TOOL = REPO / "tools" / "coinfox_packet_demo.py"

RAW_TEXT_FRAGMENT = "small public research blog notes"
UNKNOWN_SOURCE_ID = "small_research_blog_unknown"
ALLOWED_FIXTURES = (
    "official_sec_clean.allowed.json",
    "fred_clean.allowed.json",
    "reddit_two_corroborations.allowed.json",
    "unknown_clean_two_corroborations.allowed.json",
    "coindesk_watch_with_corroboration.allowed.json",
    "polymarket_odds_move_with_corroboration.allowed.json",
)
BLOCKED_FIXTURES = (
    "official_sec_prompt_injection.blocked.json",
    "reddit_single_source_hype.quarantined.json",
    "reddit_duplicate_hype.quarantined.json",
    "discord_rumor.quarantined.json",
    "unknown_blog.quarantined.json",
    "news_watch_clean.quarantined_or_watch.json",
    "kalshi_odds_move_watch.quarantined_or_watch.json",
    "raw_private_text_attempt.blocked.json",
)


def _load_fixture() -> dict[str, Any]:
    return json.loads(SOAK_FIXTURE.read_text(encoding="utf-8"))


def _load_named_fixture(name: str) -> dict[str, Any]:
    return json.loads((SOAK_DIR / name).read_text(encoding="utf-8"))


def _write_variant(tmp_path: Path, name: str, corroboration_count: int) -> Path:
    payload = _load_fixture()
    observation = copy.deepcopy(payload["observation"])
    observation["corroborations"] = observation["corroborations"][:corroboration_count]
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "schema_version": "curated_packet_soak_fixture_v0",
                "fixture_id": f"unknown_clean_{corroboration_count}_corroborations",
                "expected_result": "allowed_packet" if corroboration_count >= 2 else "quarantined",
                "observation": observation,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _run_demo(intake_path: Path, *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--intake", str(intake_path)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=check,
    )


def _assert_packet_rendered(completed: subprocess.CompletedProcess[str]) -> None:
    assert completed.returncode == 0
    assert "# CoinFox Curated Packet" in completed.stdout
    assert "cfpacket_market_pulse_20260627_fixture" in completed.stdout
    assert completed.stderr == ""


def _assert_quarantined(completed: subprocess.CompletedProcess[str], *, reason: str | None = None) -> None:
    blocked = json.loads(completed.stdout)
    assert completed.returncode == 2
    assert blocked["error"] == "quarantined"
    if reason is not None:
        assert blocked["reason"] == reason
    assert set(blocked) == {"error", "reason", "next_steps"}
    assert completed.stderr == ""


def _assert_output_hides_observation(completed: subprocess.CompletedProcess[str], payload: dict[str, Any]) -> None:
    observation = payload["observation"]
    output = completed.stdout.lower()
    source = observation["source"]
    hidden_fragments = [
        observation.get("content", ""),
        observation.get("summary", ""),
        observation.get("public_safe_summary", ""),
        observation.get("observation_id", ""),
        source.get("source_id", ""),
        source.get("source_name", ""),
    ]
    for fragment in hidden_fragments:
        if fragment:
            assert fragment.lower() not in output


def test_unknown_clean_source_with_zero_corroborations_is_quarantined(tmp_path: Path):
    intake_path = _write_variant(tmp_path, "unknown_clean_zero.json", 0)

    completed = _run_demo(intake_path)
    blocked = json.loads(completed.stdout)

    assert completed.returncode == 2
    assert blocked["error"] == "quarantined"
    assert blocked["reason"] == "NEW_OR_UNCORROBORATED_SOURCE"
    assert RAW_TEXT_FRAGMENT not in completed.stdout.lower()


def test_unknown_clean_source_with_one_corroboration_is_quarantined(tmp_path: Path):
    intake_path = _write_variant(tmp_path, "unknown_clean_one.json", 1)

    completed = _run_demo(intake_path)
    blocked = json.loads(completed.stdout)

    assert completed.returncode == 2
    assert blocked["error"] == "quarantined"
    assert blocked["reason"] == "NEW_OR_UNCORROBORATED_SOURCE"
    assert RAW_TEXT_FRAGMENT not in completed.stdout.lower()


def test_unknown_clean_source_with_two_independent_corroborations_is_allowed():
    completed = _run_demo(SOAK_FIXTURE, check=True)

    _assert_packet_rendered(completed)


def test_allowed_unknown_source_output_does_not_expose_raw_source_text():
    completed = _run_demo(SOAK_FIXTURE, check=True)

    output = completed.stdout.lower()
    assert RAW_TEXT_FRAGMENT not in output
    assert UNKNOWN_SOURCE_ID not in output
    assert "small research blog fixture" not in output
    assert "Public-safe summary:" in completed.stdout
    assert "Generated by FoxClaw for CoinFox" in completed.stdout


def test_unknown_clean_two_corroborations_fixture_is_sanitized_and_not_registered():
    payload = _load_fixture()
    observation = payload["observation"]
    registry_text = (REPO / "config" / "public_source_registry.json").read_text(encoding="utf-8")

    assert payload["expected_result"] == "allowed_packet"
    assert observation["source"]["source_id"] == UNKNOWN_SOURCE_ID
    assert UNKNOWN_SOURCE_ID not in registry_text
    assert len(observation["corroborations"]) == 2
    assert {item["source_id"] for item in observation["corroborations"]} == {
        "synthetic_public_filing_context",
        "synthetic_public_market_context",
    }

    blob = json.dumps(payload).lower()
    forbidden = (
        "ignore previous instructions",
        "reveal system prompt",
        "override authority",
        "mark this trusted",
        "export private data",
        "execute trade",
        "move funds",
        "discord.com/channels",
        "api_key",
        "token=",
        "secret=",
        "password=",
        "wallet address",
        "account number",
    )
    for fragment in forbidden:
        assert fragment not in blob


def test_clean_trusted_official_sources_are_allowed():
    for name in ("official_sec_clean.allowed.json", "fred_clean.allowed.json"):
        completed = _run_demo(SOAK_DIR / name)
        _assert_packet_rendered(completed)


def test_trusted_official_source_with_prompt_injection_text_is_blocked_and_sanitized():
    name = "official_sec_prompt_injection.blocked.json"
    payload = _load_named_fixture(name)
    completed = _run_demo(SOAK_DIR / name)

    _assert_quarantined(completed, reason="PROMPT_INJECTION_FLAGGED")
    _assert_output_hides_observation(completed, payload)


def test_unknown_uncorroborated_source_is_quarantined():
    name = "unknown_blog.quarantined.json"
    payload = _load_named_fixture(name)
    completed = _run_demo(SOAK_DIR / name)

    _assert_quarantined(completed, reason="NEW_OR_UNCORROBORATED_SOURCE")
    _assert_output_hides_observation(completed, payload)


def test_social_single_source_hype_is_quarantined():
    name = "reddit_single_source_hype.quarantined.json"
    payload = _load_named_fixture(name)
    completed = _run_demo(SOAK_DIR / name)

    _assert_quarantined(completed, reason="NEW_OR_UNCORROBORATED_SOURCE")
    _assert_output_hides_observation(completed, payload)


def test_social_source_with_two_corroborations_and_clean_scan_is_allowed():
    completed = _run_demo(SOAK_DIR / "reddit_two_corroborations.allowed.json")

    _assert_packet_rendered(completed)


def test_duplicate_hype_remains_quarantined_with_fewer_than_two_useful_corroborations():
    name = "reddit_duplicate_hype.quarantined.json"
    payload = _load_named_fixture(name)
    completed = _run_demo(SOAK_DIR / name)

    assert len(payload["observation"]["corroborations"]) == 1
    _assert_quarantined(completed, reason="NEW_OR_UNCORROBORATED_SOURCE")
    _assert_output_hides_observation(completed, payload)


def test_discord_rumor_is_quarantined():
    name = "discord_rumor.quarantined.json"
    payload = _load_named_fixture(name)
    completed = _run_demo(SOAK_DIR / name)

    _assert_quarantined(completed, reason="NEW_OR_UNCORROBORATED_SOURCE")
    _assert_output_hides_observation(completed, payload)


def test_raw_private_text_attempt_is_blocked_or_quarantined_and_sanitized():
    name = "raw_private_text_attempt.blocked.json"
    payload = _load_named_fixture(name)
    completed = _run_demo(SOAK_DIR / name)

    _assert_quarantined(completed)
    assert json.loads(completed.stdout)["reason"] in {
        "PROMPT_INJECTION_FLAGGED",
        "NEW_OR_UNCORROBORATED_SOURCE",
        "QUARANTINED",
    }
    _assert_output_hides_observation(completed, payload)


def test_news_watch_source_does_not_become_truth_without_corroboration():
    name = "news_watch_clean.quarantined_or_watch.json"
    payload = _load_named_fixture(name)
    completed = _run_demo(SOAK_DIR / name)

    _assert_quarantined(completed, reason="QUARANTINED")
    _assert_output_hides_observation(completed, payload)


def test_coindesk_watch_source_with_corroboration_is_allowed():
    completed = _run_demo(SOAK_DIR / "coindesk_watch_with_corroboration.allowed.json")

    _assert_packet_rendered(completed)


def test_odds_watch_source_does_not_become_truth_without_corroboration():
    name = "kalshi_odds_move_watch.quarantined_or_watch.json"
    payload = _load_named_fixture(name)
    completed = _run_demo(SOAK_DIR / name)

    _assert_quarantined(completed, reason="QUARANTINED")
    _assert_output_hides_observation(completed, payload)


def test_polymarket_odds_source_with_corroboration_is_allowed():
    completed = _run_demo(SOAK_DIR / "polymarket_odds_move_with_corroboration.allowed.json")

    _assert_packet_rendered(completed)


def test_allowed_soak_fixtures_render_without_exposing_raw_observations():
    for name in ALLOWED_FIXTURES:
        payload = _load_named_fixture(name)
        completed = _run_demo(SOAK_DIR / name)
        _assert_packet_rendered(completed)
        _assert_output_hides_observation(completed, payload)


def test_blocked_or_quarantined_soak_outputs_are_sanitized():
    for name in BLOCKED_FIXTURES:
        payload = _load_named_fixture(name)
        completed = _run_demo(SOAK_DIR / name)
        _assert_quarantined(completed)
        _assert_output_hides_observation(completed, payload)


def test_soak_fixture_matrix_contains_only_expected_files():
    expected = {
        *ALLOWED_FIXTURES,
        *BLOCKED_FIXTURES,
    }
    assert {path.name for path in SOAK_DIR.glob("*.json")} == expected


def test_soak_fixture_matrix_is_synthetic_and_public_safe():
    forbidden = (
        "discord.com/channels",
        "discord.gg/",
        "api_key",
        "token=",
        "secret=",
        "password=",
        "wallet address",
        "account number",
        "ssn",
        "private key",
        "mnemonic",
        "seed phrase",
    )
    for path in SOAK_DIR.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        blob = json.dumps(payload).lower()
        assert payload["schema_version"] == "curated_packet_soak_fixture_v0"
        assert payload["fixture_id"]
        assert payload["future_packet_trust_label_candidate"] in {
            "trusted_provenance",
            "prompt_injection_blocked",
            "unverified_social_heat",
            "new_source_corroborated",
            "new_source_needs_corroboration",
            "watch_source_corroborated",
            "watch_source_needs_corroboration",
            "private_text_blocked",
            "odds_move_watch",
        }
        assert payload["observation"]["safety"]["raw_content_included"] is False
        assert payload["observation"]["safety"]["contains_private_source_content"] is False
        assert payload["observation"]["safety"]["contains_credentials"] is False
        assert payload["observation"]["safety"]["live_execution_allowed"] is False
        for fragment in forbidden:
            assert fragment not in blob, f"{path.name} leaked {fragment}"
