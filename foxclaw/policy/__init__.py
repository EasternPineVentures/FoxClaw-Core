"""foxclaw.policy — safety caps, permissions, the final veto."""

from .decision_policy import POLICY_VERSION, evaluate_decision_policy

__all__ = ["evaluate_decision_policy", "POLICY_VERSION"]
