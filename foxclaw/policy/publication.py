"""Anti-poisoning publication gate between private intelligence and CoinFox."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .private_source_rules import reason_codes, scan_payload_strings

INTERNAL_ONLY = "INTERNAL_ONLY"
DERIVATIVE_PUBLIC_SAFE = "DERIVATIVE_PUBLIC_SAFE"
PUBLIC_SOURCE = "PUBLIC_SOURCE"
UNKNOWN_REVIEW = "UNKNOWN_REVIEW"

PUBLICATION_CLASSES = (INTERNAL_ONLY, DERIVATIVE_PUBLIC_SAFE, PUBLIC_SOURCE, UNKNOWN_REVIEW)

_PUBLIC_ALLOWED_CLASSES = {DERIVATIVE_PUBLIC_SAFE, PUBLIC_SOURCE}
_PRIVATE_SOURCE_CLASSES = {
    "private",
    "nonpublic",
    "founder_private",
    "discord_private",
    "raw_discord",
    "members_only",
}


@dataclass(frozen=True)
class PublicationGateResult:
    publication_class: str
    allowed: bool
    reason_codes: tuple[str, ...]
    requested_class: str
    contains_private_source_content: bool
    authority: str = "publication_gate_only"


def evaluate_publication(
    payload: Mapping[str, Any],
    *,
    requested_class: str | None = None,
) -> PublicationGateResult:
    """Evaluate whether a payload may cross into the public contract.

    The gate fails closed. Missing requested class defaults to INTERNAL_ONLY.
    Rejected items always carry at least one reason code.
    """
    if not isinstance(payload, Mapping):
        raise TypeError("publication payload must be a mapping")

    requested = _publication_class(requested_class or payload.get("publication_class"))
    if requested not in PUBLICATION_CLASSES:
        return PublicationGateResult(
            publication_class=INTERNAL_ONLY,
            allowed=False,
            reason_codes=("unsupported_publication_class",),
            requested_class=str(requested_class or payload.get("publication_class")),
            contains_private_source_content=True,
        )

    violations = list(scan_payload_strings(payload))
    reasons = list(reason_codes(violations))
    if bool(payload.get("contains_private_source_content")):
        reasons.append("contains_private_source_content")
    if _source_is_private(payload):
        reasons.append("nonpublic_source_reference")
    if _unverified_fact(payload):
        reasons.append("unverified_assertion_presented_as_fact")

    clean_reasons = tuple(dict.fromkeys(reasons))
    contains_private = bool(
        clean_reasons
        and any(
            reason
            in {
                "raw_private_discord_quotation",
                "private_message_link",
                "discord_invite_link",
                "discord_user_identifier",
                "discord_channel_identifier",
                "discord_server_identifier",
                "credential_or_token",
                "nonpublic_source_name",
                "contains_private_source_content",
                "nonpublic_source_reference",
            }
            for reason in clean_reasons
        )
    )

    if requested == INTERNAL_ONLY:
        return PublicationGateResult(
            publication_class=INTERNAL_ONLY,
            allowed=False,
            reason_codes=clean_reasons or ("default_internal_only",),
            requested_class=requested,
            contains_private_source_content=contains_private,
        )
    if requested == UNKNOWN_REVIEW:
        return PublicationGateResult(
            publication_class=UNKNOWN_REVIEW,
            allowed=False,
            reason_codes=clean_reasons or ("unknown_review_required",),
            requested_class=requested,
            contains_private_source_content=contains_private,
        )
    if clean_reasons:
        return PublicationGateResult(
            publication_class=INTERNAL_ONLY,
            allowed=False,
            reason_codes=clean_reasons,
            requested_class=requested,
            contains_private_source_content=contains_private,
        )
    if requested in _PUBLIC_ALLOWED_CLASSES:
        return PublicationGateResult(
            publication_class=requested,
            allowed=True,
            reason_codes=("public_safe",),
            requested_class=requested,
            contains_private_source_content=False,
        )

    return PublicationGateResult(
        publication_class=INTERNAL_ONLY,
        allowed=False,
        reason_codes=("default_internal_only",),
        requested_class=requested,
        contains_private_source_content=contains_private,
    )


def assert_publication_allowed(payload: Mapping[str, Any], *, requested_class: str | None = None) -> None:
    """Raise ValueError if the payload cannot cross the public gate."""
    result = evaluate_publication(payload, requested_class=requested_class)
    if not result.allowed:
        raise ValueError("publication rejected: " + ", ".join(result.reason_codes))


def _publication_class(value: Any) -> str:
    text = str(value or INTERNAL_ONLY).strip().upper().replace("-", "_").replace(" ", "_")
    return text or INTERNAL_ONLY


def _source_is_private(payload: Mapping[str, Any]) -> bool:
    candidates = (
        payload.get("source_classification"),
        payload.get("source_privacy"),
        payload.get("privacy_classification"),
    )
    private_ref = payload.get("private_source_ref")
    if isinstance(private_ref, Mapping):
        candidates = (*candidates, private_ref.get("privacy_classification"))
    return any(str(item or "").strip().lower() in _PRIVATE_SOURCE_CLASSES for item in candidates)


def _unverified_fact(payload: Mapping[str, Any]) -> bool:
    status = str(
        payload.get("verification_status")
        or payload.get("claim_status")
        or payload.get("validation_status")
        or ""
    ).strip().lower()
    presentation = str(payload.get("presentation") or payload.get("assertion_mode") or "").strip().lower()
    return status in {"unverified", "unknown", "rumor"} and presentation in {"fact", "confirmed"}
