"""Public-safe Packet Trust Metadata V0 labels for curated packet intake."""

from __future__ import annotations

from typing import Any, Mapping

SCHEMA_VERSION = "packet_trust_metadata.v0"

AUTHORITY_LOCKS = {
    "can_train_model": False,
    "can_update_verified_memory": False,
    "can_change_source_reliability": False,
    "can_promote_evidence": False,
    "can_authorize_execution": False,
    "can_submit_order": False,
    "can_move_funds": False,
    "live_execution_allowed": False,
}

LABEL_DEFINITIONS = {
    "trusted_provenance": {
        "display_label": "Trusted provenance",
        "public_note": "Known public provenance passed the V0 guard.",
        "operator_note": "Trusted source still required a clean prompt-injection scan.",
    },
    "prompt_injection_blocked": {
        "display_label": "Prompt injection blocked",
        "public_note": "Instruction-like source text was blocked before packet rendering.",
        "operator_note": "Review the source manually before any future summary attempt.",
    },
    "unverified_social_heat": {
        "display_label": "Unverified social heat",
        "public_note": "Public social attention is context, not truth.",
        "operator_note": "Treat this as review context even when corroboration lets it pass.",
    },
    "new_source_corroborated": {
        "display_label": "New source, corroborated",
        "public_note": "A new public source passed only after independent corroboration.",
        "operator_note": "Do not turn this into source reputation without outcome review.",
    },
    "new_source_needs_corroboration": {
        "display_label": "New source, needs corroboration",
        "public_note": "A new public source needs independent corroboration before influence.",
        "operator_note": "Keep quarantined until at least two independent corroborations exist.",
    },
    "watch_source_corroborated": {
        "display_label": "Watch source, corroborated",
        "public_note": "A watch source became review material after corroboration.",
        "operator_note": "Useful context, not automatic truth or source promotion.",
    },
    "watch_source_needs_corroboration": {
        "display_label": "Watch source, needs corroboration",
        "public_note": "A watch source needs independent corroboration before influence.",
        "operator_note": "Keep as watch-only context until corroboration exists.",
    },
    "private_text_blocked": {
        "display_label": "Private text blocked",
        "public_note": "A private-text export attempt was blocked before packet rendering.",
        "operator_note": "Do not expose raw private source text in public packet output.",
    },
    "odds_move_watch": {
        "display_label": "Odds move watch",
        "public_note": "Prediction-market odds are context, not settled truth.",
        "operator_note": "Require public corroboration and outcome review before learning.",
    },
}

PRIVATE_TEXT_MARKERS = (
    "private-text",
    "private text",
    "private-source",
    "private source",
    "private data",
    "export private",
)

SOCIAL_SOURCE_MARKERS = ("social", "community")
PREDICTION_MARKET_MARKERS = ("prediction_market", "prediction market", "odds")


def build_packet_trust_metadata(
    observation: Mapping[str, Any],
    source_state: Mapping[str, Any],
    scan_result: Mapping[str, Any],
    decision: Mapping[str, Any],
    corroboration_count: int = 0,
) -> dict[str, object]:
    """Build sanitized trust metadata from an already-evaluated intake observation.

    V0 intentionally emits labels and guard facts only. It does not include raw source text,
    source IDs, source URLs, scores, confidence values, or reputation mutations.
    """
    count = max(0, int(corroboration_count or 0))
    allowed = bool(decision.get("allowed"))
    prompt_injection_flagged = bool(scan_result.get("flagged"))
    source_type = _source_type_for(observation, source_state)
    trust_state = _trust_state_for(source_state)
    label = classify_packet_trust_label(
        observation=observation,
        source_state=source_state,
        source_type=source_type,
        trust_state=trust_state,
        prompt_injection_flagged=prompt_injection_flagged,
        allowed=allowed,
        corroboration_count=count,
    )
    display = LABEL_DEFINITIONS[label]

    return {
        "schema_version": SCHEMA_VERSION,
        "label": label,
        "display": dict(display),
        "source_type": source_type,
        "trust_state": trust_state,
        "corroboration_count": count,
        "prompt_injection_flagged": prompt_injection_flagged,
        "allowed_by_guard": allowed,
        "decision_reason": str(decision.get("reason", "UNKNOWN_DECISION")),
        "public_safe_source": bool(source_state.get("public_safe", False)),
        "authority": dict(AUTHORITY_LOCKS),
    }


def classify_packet_trust_label(
    *,
    observation: Mapping[str, Any],
    source_state: Mapping[str, Any],
    source_type: str,
    trust_state: str,
    prompt_injection_flagged: bool,
    allowed: bool,
    corroboration_count: int,
) -> str:
    """Return the V0 public-safe trust label for one evaluated observation."""
    text = _observation_scan_text(observation).casefold()
    source_type_folded = source_type.casefold()

    if any(marker in text for marker in PRIVATE_TEXT_MARKERS):
        return "private_text_blocked"
    if prompt_injection_flagged:
        return "prompt_injection_blocked"
    if any(marker in source_type_folded for marker in PREDICTION_MARKET_MARKERS):
        return "odds_move_watch"
    if any(marker in source_type_folded for marker in SOCIAL_SOURCE_MARKERS):
        return "unverified_social_heat"
    if _is_unknown_source(source_state, trust_state):
        if allowed and corroboration_count >= 2:
            return "new_source_corroborated"
        return "new_source_needs_corroboration"
    if trust_state == "watch":
        if allowed and corroboration_count >= 2:
            return "watch_source_corroborated"
        return "watch_source_needs_corroboration"
    if trust_state == "trusted":
        return "trusted_provenance"
    if allowed:
        return "watch_source_corroborated"
    return "new_source_needs_corroboration"


def render_packet_trust_metadata_markdown(metadata: list[Mapping[str, Any]]) -> str:
    """Render sanitized metadata for operator demos without raw intake text."""
    if not metadata:
        return "## Packet Trust Metadata V0\n\nNo intake observations were evaluated."

    lines = ["## Packet Trust Metadata V0", ""]
    for index, item in enumerate(metadata, start=1):
        display = item.get("display")
        display = display if isinstance(display, Mapping) else {}
        label = str(item.get("label", "unknown_label"))
        display_label = str(display.get("display_label", label))
        public_note = str(display.get("public_note", ""))
        source_type = str(item.get("source_type", "unknown"))
        trust_state = str(item.get("trust_state", "unknown"))
        decision_reason = str(item.get("decision_reason", "UNKNOWN_DECISION"))
        allowed = str(bool(item.get("allowed_by_guard"))).lower()
        count = int(item.get("corroboration_count", 0) or 0)
        lines.extend(
            [
                f"### Observation {index}: {display_label}",
                "",
                f"- Label: `{label}`",
                f"- Source type: `{source_type}`",
                f"- Trust state: `{trust_state}`",
                f"- Corroborations: `{count}`",
                f"- Guard allowed: `{allowed}`",
                f"- Decision reason: `{decision_reason}`",
                f"- Public note: {public_note}",
                "- Authority: `review_only_no_execution_no_memory_mutation`",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _source_type_for(
    observation: Mapping[str, Any],
    source_state: Mapping[str, Any],
) -> str:
    source = observation.get("source")
    source = source if isinstance(source, Mapping) else {}
    source_type = (
        source_state.get("source_type")
        or source.get("source_type")
        or observation.get("source_type")
        or "unknown"
    )
    source_type_text = str(source_type).strip() or "unknown"
    if source_type_text == "unknown":
        observed_source_type = source.get("source_type") or observation.get("source_type")
        if observed_source_type:
            return str(observed_source_type).strip() or "unknown"
    return source_type_text


def _trust_state_for(source_state: Mapping[str, Any]) -> str:
    return str(source_state.get("trust_state", "unknown")).strip().lower() or "unknown"


def _is_unknown_source(source_state: Mapping[str, Any], trust_state: str) -> bool:
    return trust_state == "quarantined" and source_state.get("public_safe") is False


def _observation_scan_text(observation: Mapping[str, Any]) -> str:
    parts = []
    for field in ("text", "content", "summary", "public_safe_summary"):
        value = observation.get(field)
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)
