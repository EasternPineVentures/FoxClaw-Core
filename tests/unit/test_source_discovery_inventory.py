from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from foxclaw.source_discovery import build_report, load_inventory

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "source_discovery_inventory.py"


def test_source_discovery_inventory_has_broad_coverage_and_authority_locks():
    report = build_report(generated_at=datetime(2026, 6, 30, 15, 0, tzinfo=UTC))

    assert report["schema_version"] == "source_discovery_report.v0"
    assert report["source_count"] >= 65
    assert report["reddit_source_count"] >= 15
    assert report["fast_manual_count"] >= 10
    assert report["authority"] == {
        "can_submit_order": False,
        "can_move_funds": False,
        "live_execution_allowed": False,
        "can_publish_to_coinfox": False,
        "can_change_source_reliability": False,
        "can_update_verified_memory": False,
        "can_train_model": False,
    }


def test_source_discovery_inventory_categories_include_fast_research_lanes():
    report = build_report(generated_at=datetime(2026, 6, 30, 15, 0, tzinfo=UTC))
    categories = report["category_counts"]

    for category in (
        "coinfox_native",
        "reddit",
        "social_market",
        "official_regulatory",
        "official_macro",
        "professional_news",
        "prediction_markets",
        "crypto_onchain",
        "alternative_attention",
    ):
        assert category in categories


def test_reddit_sources_are_social_heat_only_until_corroborated():
    inventory = load_inventory()
    reddit_sources = [source for source in inventory["sources"] if source.category == "reddit"]

    assert len(reddit_sources) >= 15
    for source in reddit_sources:
        assert source.trust_state == "quarantined"
        assert source.source_type == "social_community"
        assert source.requires_corroboration_count == 2
        assert source.public_safe_default is True


def test_official_sources_are_trusted_provenance_not_authority():
    inventory = load_inventory()
    official_sources = [
        source
        for source in inventory["sources"]
        if source.category in {"official_regulatory", "official_macro", "official_market"}
    ]

    assert official_sources
    assert any(source.id == "sec_edgar_company_filings" for source in official_sources)
    assert any(source.id == "fred_macro_data" for source in official_sources)
    for source in official_sources:
        assert source.trust_state == "trusted"
        assert source.public_safe_default is True


def test_source_discovery_cli_fixture_json_is_parseable():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--json", "--limit", "12"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["generated_at"] == "2026-06-30T15:00:00Z"
    assert payload["source_count"] >= 65
    assert len(payload["top_sources"]) == 12
    assert payload["reddit_source_count"] >= 15


def test_source_discovery_cli_fixture_markdown_names_reddit_and_authority():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--limit", "8"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "# Source Discovery Inventory" in completed.stdout
    assert "## Reddit Watchlist" in completed.stdout
    assert "Reddit r/wallstreetbets" in completed.stdout
    assert "`can_publish_to_coinfox=false`" in completed.stdout


def test_source_discovery_inventory_rejects_bad_authority(tmp_path):
    manifest = {
        "schema_version": "source_discovery_inventory.v0",
        "updated_at": "2026-06-30",
        "generated_for": "test",
        "authority": {
            "can_submit_order": True,
            "can_move_funds": False,
            "live_execution_allowed": False,
            "can_publish_to_coinfox": False,
            "can_change_source_reliability": False,
            "can_update_verified_memory": False,
            "can_train_model": False,
        },
        "sources": [],
    }
    path = tmp_path / "bad_inventory.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="can_submit_order=false"):
        load_inventory(path)
