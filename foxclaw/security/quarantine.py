"""Quarantine decisions for raw source observations."""

from __future__ import annotations

from typing import Any, Mapping


def default_source_state(source_id: str, source_type: str = "unknown") -> dict[str, object]:
    """Return the default state for a source before it earns public influence."""
    return {
        "source_id": source_id,
        "source_type": source_type,
        "trust_state": "quarantined",
        "can_influence_public_packet": False,
        "can_train_model": False,
        "can_update_verified_memory": False,
        "observation_count": 0,
    }


def quarantine_decision(
    observation: dict[str, Any],
    source_state: Mapping[str, Any],
    corroboration_count: int = 0,
    prompt_injection_flagged: bool = False,
) -> dict[str, object]:
    """Decide whether an observation may influence public packet creation."""
    _ = observation
    trust_state = str(source_state.get("trust_state", "")).strip().lower()
    count = max(0, int(corroboration_count or 0))

    if prompt_injection_flagged:
        return _decision(
            allowed=False,
            reason="PROMPT_INJECTION_FLAGGED",
            next_steps=[
                "keep_in_quarantine",
                "remove_or_summarize_instruction_like_text",
                "operator_review_required",
            ],
        )
    if trust_state == "trusted":
        return _decision(
            allowed=True,
            reason="TRUSTED_SOURCE",
            next_steps=["continue_to_public_packet_review"],
        )
    if trust_state == "quarantined" and count < 2:
        return _decision(
            allowed=False,
            reason="NEW_OR_UNCORROBORATED_SOURCE",
            next_steps=[
                "keep_in_quarantine",
                "wait_for_two_independent_corroborations",
                "operator_review_required",
            ],
        )
    if count >= 2:
        return _decision(
            allowed=True,
            reason="CORROBORATED_SOURCE",
            next_steps=["continue_to_public_packet_review", "preserve_counterpoint"],
        )
    return _decision(
        allowed=False,
        reason="QUARANTINED",
        next_steps=["keep_in_quarantine", "operator_review_required"],
    )


def _decision(allowed: bool, reason: str, next_steps: list[str]) -> dict[str, object]:
    return {
        "allowed": allowed,
        "reason": reason,
        "next_steps": next_steps,
    }
