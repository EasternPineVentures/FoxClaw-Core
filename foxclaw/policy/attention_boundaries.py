"""Attention permissions: attention may prioritize review, never truth."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

ALLOWED_ATTENTION_EFFECTS = frozenset(
    {
        "raise_review_priority",
        "create_trending_flag",
        "trigger_evidence_refresh",
        "trigger_price_response_analysis",
    }
)

FORBIDDEN_ATTENTION_EFFECTS = frozenset(
    {
        "increase_source_trust",
        "promote_evidence",
        "alter_edge",
        "increase_sizing",
        "authorize_execution",
        "change_truth",
    }
)


@dataclass(frozen=True)
class AttentionBoundaryResult:
    allowed_effects: tuple[str, ...]
    rejected_effects: tuple[str, ...]
    reason_codes: tuple[str, ...]
    authority: str = "review_priority_only"

    @property
    def allowed(self) -> bool:
        return not self.rejected_effects


def evaluate_attention_effects(requested_effects: Mapping[str, bool]) -> AttentionBoundaryResult:
    """Evaluate requested attention effects and reject authority drift."""
    allowed: list[str] = []
    rejected: list[str] = []
    reasons: list[str] = []

    for effect, enabled in sorted(requested_effects.items()):
        if not enabled:
            continue
        key = str(effect).strip().lower()
        if key in ALLOWED_ATTENTION_EFFECTS:
            allowed.append(key)
        elif key in FORBIDDEN_ATTENTION_EFFECTS:
            rejected.append(key)
            reasons.append(f"attention_cannot_{key}")
        else:
            rejected.append(key)
            reasons.append("unknown_attention_effect")

    return AttentionBoundaryResult(
        allowed_effects=tuple(allowed),
        rejected_effects=tuple(rejected),
        reason_codes=tuple(dict.fromkeys(reasons)) or ("attention_review_priority_only",),
    )


def attention_may(effect: str) -> bool:
    """Return whether attention is allowed to cause one effect."""
    return str(effect).strip().lower() in ALLOWED_ATTENTION_EFFECTS
