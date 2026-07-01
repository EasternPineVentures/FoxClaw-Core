"""Interaction Potential V0 scoring for CoinFox packet observations.

The score predicts discussion energy, not evidence quality or truth.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "interaction_potential_v0.json"
DEFAULT_INTAKE_FIXTURE = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "fixtures"
    / "coinfox_packet_intake"
    / "manual_market_pulse_intake.valid.json"
)
AUTHORITY_KEYS = (
    "can_submit_order",
    "can_move_funds",
    "live_execution_allowed",
    "can_publish_to_coinfox",
    "can_change_truth",
    "can_promote_evidence",
    "can_change_source_reliability",
    "can_update_verified_memory",
    "can_train_model",
)
SOCIAL_SOURCE_TYPES = {
    "community",
    "social_community",
    "public_user_post",
    "public_user_thesis",
    "public_challenge",
    "attention_signal",
    "creator_media",
}


@dataclass(frozen=True)
class DriverConfig:
    id: str
    weight: int
    meaning: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DriverConfig":
        for field in ("id", "weight", "meaning"):
            if field not in payload:
                raise ValueError(f"interaction driver missing {field}")
        weight = int(payload["weight"])
        if weight < 0 or weight > 100:
            raise ValueError(f"interaction driver weight out of range: {payload['id']}")
        return cls(id=str(payload["id"]), weight=weight, meaning=str(payload["meaning"]))


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("schema_version") != "interaction_potential.v0":
        raise ValueError("interaction potential config must use schema_version interaction_potential.v0")
    _validate_authority(config.get("authority", {}))
    drivers = [DriverConfig.from_dict(item) for item in config.get("drivers", [])]
    if not drivers:
        raise ValueError("interaction potential config must contain drivers")
    if sum(driver.weight for driver in drivers) != 100:
        raise ValueError("interaction potential driver weights must sum to 100")
    config["drivers"] = drivers
    return config


def score_intake_payload(
    payload: Mapping[str, Any],
    *,
    config: Mapping[str, Any] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    active_config = dict(config) if config is not None else load_config()
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0)
    observations = list(_iter_observations(payload))
    scores = [
        score_observation(observation, active_config)
        for observation in observations
    ]
    ranked = sorted(scores, key=lambda item: (-int(item["score"]), str(item["target_card_id"])))

    return {
        "schema_version": "interaction_potential_report.v0",
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "generated_for": active_config["generated_for"],
        "decision_boundary": "ranking_only_not_truth_not_evidence",
        "authority": active_config["authority"],
        "observation_count": len(observations),
        "scores": ranked,
        "top_score": ranked[0] if ranked else None,
    }


def score_observation(
    observation: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    active_config = dict(config) if config is not None else load_config()
    drivers: list[dict[str, Any]] = []
    for driver in active_config["drivers"]:
        points, reason = _score_driver(driver, observation, active_config)
        drivers.append(
            {
                "id": driver.id,
                "points": points,
                "max_points": driver.weight,
                "reason": reason,
            }
        )
    score = min(100, sum(int(driver["points"]) for driver in drivers))
    return {
        "schema_version": "interaction_potential.v0",
        "target_card_id": str(observation.get("target_card_id", "unmapped_observation")),
        "asset_or_topic": str(observation.get("asset_or_topic", "unknown")),
        "score": score,
        "label": _band_for_score(score, active_config),
        "drivers": drivers,
        "authority": active_config["authority"],
        "decision_boundary": "interaction_ranking_only",
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Interaction Potential",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Observations: `{report['observation_count']}`",
        f"Boundary: `{report['decision_boundary']}`",
        "",
        "## Ranked Candidates",
        "",
    ]
    for item in report["scores"]:
        positive = [
            f"{driver['id']}={driver['points']}"
            for driver in item["drivers"]
            if int(driver["points"]) > 0
        ]
        lines.extend(
            [
                f"- `{item['target_card_id']}` / `{item['asset_or_topic']}`: "
                f"`{item['score']}` ({item['label']})",
                f"  Drivers: {', '.join(positive) if positive else 'none'}",
            ]
        )
    lines.extend(
        [
            "",
            "## Authority",
            "",
            "- `can_submit_order=false`",
            "- `can_move_funds=false`",
            "- `live_execution_allowed=false`",
            "- `can_publish_to_coinfox=false`",
            "- `can_change_truth=false`",
            "- `can_promote_evidence=false`",
            "- `can_change_source_reliability=false`",
            "- `can_update_verified_memory=false`",
            "- `can_train_model=false`",
            "",
        ]
    )
    return "\n".join(lines)


def _score_driver(
    driver: DriverConfig,
    observation: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[int, str]:
    driver_id = driver.id
    if driver_id == "clear_public_prompt":
        prompt = str(observation.get("suggested_coinfox_prompt", "")).strip()
        if prompt and ("?" in prompt or len(prompt) >= 35):
            return driver.weight, "clear_coinfox_prompt"
        if prompt:
            return driver.weight // 2, "prompt_present_but_soft"
        return 0, "missing_prompt"

    if driver_id == "counterpoint_or_disagreement":
        if str(observation.get("counterpoint", "")).strip():
            return driver.weight, "counterpoint_present"
        return 0, "missing_counterpoint"

    if driver_id == "social_attention_or_native_conversation":
        source_type = _source_type(observation)
        reason_codes = _reason_codes(observation)
        risk_flags = _list_text(observation.get("risk_flags"))
        if source_type in SOCIAL_SOURCE_TYPES:
            return driver.weight, "social_or_native_conversation_source"
        if "social_heat_only" in reason_codes or "social_heat_not_evidence" in risk_flags:
            return driver.weight, "social_heat_flag"
        if source_type in {"prediction_market", "public_market_info"}:
            return driver.weight // 2, "market_context_can_prompt_discussion"
        return 0, "not_conversation_native"

    if driver_id == "timely_change_or_delta":
        haystack = _observation_text(observation)
        reason_codes = _reason_codes(observation)
        if "daily_delta" in reason_codes or "prediction_market_move" in reason_codes:
            return driver.weight, "reason_code_signals_delta"
        if _has_keyword(haystack, config, "timely_change_or_delta"):
            return driver.weight, "text_signals_change"
        return 0, "no_clear_delta"

    if driver_id == "money_or_position_relevance":
        haystack = _observation_text(observation)
        source_type = _source_type(observation)
        if source_type in {"prediction_market", "market_data", "company_public", "official_regulatory"}:
            return driver.weight, "market_or_company_source"
        if str(observation.get("asset_or_topic", "")).strip():
            return driver.weight, "asset_or_topic_present"
        if _has_keyword(haystack, config, "money_or_position_relevance"):
            return driver.weight, "market_keyword_present"
        return 0, "no_market_relevance"

    if driver_id == "uncertainty_or_open_question":
        prompt = str(observation.get("suggested_coinfox_prompt", ""))
        confidence = str(observation.get("confidence", "")).strip().lower()
        haystack = f"{prompt}\n{_observation_text(observation)}"
        if "?" in prompt:
            return driver.weight, "prompt_is_question"
        if confidence in {"low", "medium"}:
            return driver.weight, "uncertain_confidence"
        if _has_keyword(haystack, config, "uncertainty_or_open_question"):
            return driver.weight, "uncertainty_keyword_present"
        return 0, "closed_or_overcertain"

    if driver_id == "source_diversity_context":
        corroborations = observation.get("corroborations", [])
        count = len(corroborations) if isinstance(corroborations, list) else 0
        if count >= 2:
            return driver.weight, "two_or_more_public_corroborations"
        if count == 1:
            return max(1, driver.weight // 2), "one_public_corroboration"
        return 0, "no_corroboration_context"

    if driver_id == "outcome_reviewable":
        outcome = observation.get("outcome_review")
        outcome = outcome if isinstance(outcome, Mapping) else {}
        if outcome.get("review_question") and outcome.get("review_after"):
            return driver.weight, "outcome_review_question_present"
        if outcome.get("review_question"):
            return max(1, driver.weight // 2), "outcome_question_present_without_date"
        return 0, "missing_outcome_review"

    return 0, "unknown_driver"


def _iter_observations(payload: Mapping[str, Any]):
    observations = payload.get("source_observations")
    if isinstance(observations, list):
        for observation in observations:
            if isinstance(observation, Mapping):
                yield observation
        return
    observation = payload.get("observation")
    if isinstance(observation, Mapping):
        yield observation
        return
    yield payload


def _source_type(observation: Mapping[str, Any]) -> str:
    source = observation.get("source")
    source = source if isinstance(source, Mapping) else {}
    return str(source.get("source_type") or observation.get("source_type") or "").strip().lower()


def _reason_codes(observation: Mapping[str, Any]) -> set[str]:
    curation = observation.get("curation_decision")
    curation = curation if isinstance(curation, Mapping) else {}
    return set(_list_text(curation.get("reason_codes")))


def _list_text(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip().lower() for item in value if str(item).strip()]


def _observation_text(observation: Mapping[str, Any]) -> str:
    fields = (
        "asset_or_topic",
        "what_happened",
        "why_interesting",
        "public_safe_summary",
        "counterpoint",
        "suggested_thesis_angle",
        "suggested_coinfox_prompt",
    )
    return "\n".join(str(observation.get(field, "")) for field in fields).casefold()


def _has_keyword(text: str, config: Mapping[str, Any], key: str) -> bool:
    keyword_hints = config.get("keyword_hints")
    keyword_hints = keyword_hints if isinstance(keyword_hints, Mapping) else {}
    keywords = keyword_hints.get(key, [])
    return any(str(keyword).casefold() in text for keyword in keywords)


def _band_for_score(score: int, config: Mapping[str, Any]) -> str:
    for band in config.get("bands", []):
        if int(band["min_score"]) <= score <= int(band["max_score"]):
            return str(band["label"])
    return "unbanded"


def _validate_authority(authority: Mapping[str, Any]) -> None:
    for key in AUTHORITY_KEYS:
        if authority.get(key) is not False:
            raise ValueError(f"interaction potential authority must keep {key}=false")
