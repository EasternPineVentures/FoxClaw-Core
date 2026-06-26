from __future__ import annotations

import json

from tools.build_public_demo_site import build_site


def test_build_public_demo_site_writes_static_site_and_export(tmp_path) -> None:
    output = tmp_path / "site"

    result = build_site(output)

    assert result["public_safe"] is True
    assert result["paper_only"] is True
    assert result["card_count"] == 6
    assert result["outcome_count"] == 1
    assert (output / "index.html").exists()
    assert (output / "styles.css").exists()
    assert (output / "README.txt").exists()
    assert (output / "coinfox-export" / "manifest.json").exists()
    assert (output / "coinfox-export" / "intelligence_cards.jsonl").exists()
    assert (output / "coinfox-export" / "scorecard.json").exists()
    assert (output / "coinfox-export" / "outcomes.jsonl").exists()


def test_build_public_demo_site_keeps_public_safety_language(tmp_path) -> None:
    output = tmp_path / "site"

    build_site(output)

    html = (output / "index.html").read_text(encoding="utf-8")
    manifest = json.loads((output / "coinfox-export" / "manifest.json").read_text())

    assert "Not individualized advice" in html
    assert "No live orders" in html
    assert "No funds movement" in html
    assert "No private Discord archive" in html
    assert manifest["status"]["live_execution_allowed"] is False
    assert manifest["status"]["not_individualized_advice"] is True
