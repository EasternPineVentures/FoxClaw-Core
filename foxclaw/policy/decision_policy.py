"""Decision policy — the allow / escalate_hold / block veto on what a decision may be.

Ported from v1 ``src/policy/fc_decision_policy.py`` unchanged in behavior. This enforces
invariant #1 (paper-only): every execution/funds/secret decision type is *blocked* here,
so no decision receipt can authorize live action. Domain-neutral by construction
(invariant #4) — it speaks decisions and domains, not market words.
"""
from __future__ import annotations

from typing import Any

POLICY_VERSION = "decision_policy_v0"

ALLOWED_DECISION_TYPES = {
    "hold",
    "watch",
    "ignore",
    "escalate",
    "paper_candidate_intent",
    "paper_candidate_request",
}
BLOCKED_DECISION_TYPES = {
    "paper_trade_long",
    "paper_trade_short",
    "live_trade",
    "submit_order",
    "buy",
    "sell",
    "execute",
    "fund_move",
    "rotate_secret",
    "mutate_grove_directly",
}
ALLOWED_DOMAINS = {
    "source_intake",
    "parsing",
    "candidate_generation",
    "decision_receipt",
    "paper_trading_simulation",
    "learning_scoring",
    "command_center",
    "apollo_task_routing",
    "local_llm_reasoning",
    "repo_delivery",
    "manual_live_exposure_tracking",
    "live_canary_readiness",
}
ESCALATE_DOMAINS = {
    "vendor_spend",
    "timeline",
    "scope_product_direction",
    "canary_preparation",
}
BLOCKED_DOMAINS = {
    "live_trading",
    "funds_movement",
    "secret_rotation",
    "destructive_data_action",
}


def _clean(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def evaluate_decision_policy(
    *,
    domain: str = "decision_receipt",
    action: str = "create_decision_receipt",
    decision_type: str = "",
    actor: str = "foxclaw",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an allow/escalate_hold/block policy decision for a proposed action."""
    domain_key = _clean(domain)
    action_key = _clean(action)
    decision_key = _clean(decision_type)
    data = dict(metadata or {})

    result = "allow"
    authority_level = "A2_guarded_record"
    reason = "Action is inside FoxClaw guarded receipt boundaries."

    if decision_key in BLOCKED_DECISION_TYPES or domain_key in BLOCKED_DOMAINS:
        result = "block"
        authority_level = "A4_prohibited"
        reason = "Action is prohibited before explicit future authority gates."
    elif action_key in {"llm_trade_approval", "local_llm_trade_approval"}:
        result = "block"
        authority_level = "A4_prohibited"
        reason = "LLM output cannot authorize execution."
    elif domain_key in ESCALATE_DOMAINS or bool(data.get("authority_shift")):
        result = "escalate_hold"
        authority_level = "A3_escalate_hold"
        reason = "Action changes spend, timing, scope, or authority and requires operator review."
    elif decision_key == "escalate":
        result = "escalate_hold"
        authority_level = "A3_escalate_hold"
        reason = "Escalation decision is recorded as hold-for-review."
    elif decision_key and decision_key not in ALLOWED_DECISION_TYPES:
        result = "block"
        authority_level = "A4_prohibited"
        reason = f"Unsupported decision_type: {decision_type}"
    elif domain_key and domain_key not in ALLOWED_DOMAINS:
        result = "escalate_hold"
        authority_level = "A3_escalate_hold"
        reason = f"Unrecognized policy domain requires operator review: {domain}"

    return {
        "policy_version": POLICY_VERSION,
        "policy_result": result,
        "authority_level": authority_level,
        "domain": domain_key,
        "action": action_key,
        "decision_type": decision_key,
        "actor": str(actor or "foxclaw"),
        "reason": reason,
    }
