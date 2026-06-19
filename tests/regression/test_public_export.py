from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from foxclaw.contract.public import PUBLIC_CONTRACT_VERSION
from foxclaw.contract.public.export import load_fixture_cards, load_fixture_outcomes
from foxclaw.policy.publication import evaluate_publication

REPO = Path(__file__).resolve().parents[2]
EXPORT_TOOL = REPO / "tools" / "export_public_intelligence.py"
SCORECARD_TOOL = REPO / "tools" / "export_public_scorecard.py"
FIXTURE_DIR = REPO / "tests" / "fixtures" / "public_contract"


def test_public_export_writes_coinfox_reference_files(tmp_path: Path):
    out = tmp_path / "coinfox"
    completed = subprocess.run(
        [sys.executable, str(EXPORT_TOOL), "--fixture", "--output", str(out)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    summary = json.loads(completed.stdout)
    assert summary["card_count"] == 6
    assert summary["outcome_count"] == 1

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["contract_version"] == PUBLIC_CONTRACT_VERSION == "1.0.0"
    assert manifest["author_display"] == "FoxClaw"
    assert manifest["mode"] == "informational_paper"
    assert manifest["counts"] == {"intelligence_cards": 6, "outcomes": 1}

    card_lines = (out / "intelligence_cards.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(card_lines) == 6
    cards = [json.loads(line) for line in card_lines]
    assert {card["risk_class"] for card in cards} >= {
        "WATCH",
        "STRUCTURED",
        "SPECULATIVE",
        "REDLINE",
        "REJECT",
    }
    for card in cards:
        result = evaluate_publication(card)
        assert result.allowed is True
        assert card["contract_version"] == "1.0.0"
        assert card["author_display"] == "FoxClaw"
        assert card["mode"] == "informational_paper"
        assert card["contains_private_source_content"] is False
        assert card["status"]["live_execution_allowed"] is False
        assert card["public_explanation"]["not_individualized_advice"] is True

    scorecard = json.loads((out / "scorecard.json").read_text(encoding="utf-8"))
    assert scorecard["schema_version"] == "public_scorecard_export.v1"
    assert len(scorecard["entries"]) == 6
    assert scorecard["status"]["live_execution_allowed"] is False

    outcome_lines = (out / "outcomes.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(outcome_lines) == 1
    outcome = json.loads(outcome_lines[0])
    assert outcome["schema_version"] == "verified_outcome.v1"
    assert outcome["status"]["not_individualized_advice"] is True


def test_public_scorecard_tool_emits_deterministic_fixture_scorecard():
    completed = subprocess.run(
        [sys.executable, str(SCORECARD_TOOL), "--fixture"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    scorecard = json.loads(completed.stdout)
    assert scorecard["contract_version"] == "1.0.0"
    assert [entry["public_intelligence_id"] for entry in scorecard["entries"]] == sorted(
        entry["public_intelligence_id"] for entry in scorecard["entries"]
    )


def test_fixture_export_inputs_are_public_contract_objects():
    cards = load_fixture_cards(FIXTURE_DIR)
    outcomes = load_fixture_outcomes(FIXTURE_DIR)
    assert len(cards) == 6
    assert len(outcomes) == 1
    assert all(card["schema_version"] == "public_intelligence_card.v1" for card in cards)
    assert all(outcome["schema_version"] == "verified_outcome.v1" for outcome in outcomes)
