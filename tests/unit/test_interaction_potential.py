from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from foxclaw.interaction_potential import load_config, score_intake_payload, score_observation

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "interaction_potential.py"
FIXTURE = (
    REPO / "tests" / "fixtures" / "coinfox_packet_intake" / "manual_market_pulse_intake.valid.json"
)


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_interaction_potential_config_weights_and_authority_locks():
    config = load_config()

    assert sum(driver.weight for driver in config["drivers"]) == 100
    assert config["authority"] == {
        "can_submit_order": False,
        "can_move_funds": False,
        "live_execution_allowed": False,
        "can_publish_to_coinfox": False,
        "can_change_truth": False,
        "can_promote_evidence": False,
        "can_change_source_reliability": False,
        "can_update_verified_memory": False,
        "can_train_model": False,
    }


def test_interaction_potential_ranks_manual_packet_observations():
    report = score_intake_payload(
        _load_fixture(),
        generated_at=datetime(2026, 7, 1, 15, 0, tzinfo=UTC),
    )

    assert report["schema_version"] == "interaction_potential_report.v0"
    assert report["decision_boundary"] == "ranking_only_not_truth_not_evidence"
    assert report["observation_count"] == 3
    assert [item["target_card_id"] for item in report["scores"]] == [
        "cfcard_wen_social_spark_fixture",
        "cfcard_prediction_market_gap_fixture",
        "cfcard_btc_macro_delta_fixture",
    ]
    assert report["scores"][0]["score"] == 100
    assert report["scores"][0]["label"] == "high_reaction_potential"
    assert report["scores"][1]["score"] > report["scores"][2]["score"]


def test_interaction_potential_output_does_not_expose_raw_observation_text_or_sources():
    report = score_intake_payload(_load_fixture())
    blob = json.dumps(report).lower()

    forbidden = (
        "retail attention around wen is being tracked",
        "https://coinfox.foxclaw.cloud/",
        "coinfox manual market pulse board",
        "a public prediction-market move is being reviewed",
        "the useful btc discussion shifted",
        "kalshi.com",
        "coinfox markets",
    )
    for fragment in forbidden:
        assert fragment not in blob


def test_sparse_observation_scores_low_and_cannot_gain_authority():
    score = score_observation(
        {
            "asset_or_topic": "QUIET",
            "suggested_coinfox_prompt": "",
            "corroborations": [],
            "safety": {"live_execution_allowed": False},
        }
    )

    assert score["score"] < 40
    assert score["label"] == "low_interaction_potential"
    assert all(value is False for value in score["authority"].values())


def test_interaction_potential_cli_fixture_json_is_parseable():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture", "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["generated_at"] == "2026-07-01T15:00:00Z"
    assert payload["top_score"]["target_card_id"] == "cfcard_wen_social_spark_fixture"
    assert payload["top_score"]["score"] == 100
    assert payload["authority"]["can_publish_to_coinfox"] is False


def test_interaction_potential_cli_fixture_markdown_names_boundary():
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--fixture"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "# Interaction Potential" in completed.stdout
    assert "`ranking_only_not_truth_not_evidence`" in completed.stdout
    assert "cfcard_wen_social_spark_fixture" in completed.stdout
    assert "`can_change_truth=false`" in completed.stdout


def test_interaction_potential_rejects_bad_authority(tmp_path):
    config = json.loads((REPO / "config" / "interaction_potential_v0.json").read_text(encoding="utf-8"))
    config["authority"]["can_change_truth"] = True
    path = tmp_path / "bad_interaction_config.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ValueError, match="can_change_truth=false"):
        load_config(path)
