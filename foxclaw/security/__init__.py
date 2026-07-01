"""Small security rails for FoxClaw intake and public packet preparation."""

from .prompt_injection import FLAG_PHRASES, scan
from .quarantine import default_source_state, quarantine_decision
from .packet_trust_metadata import (
    build_packet_trust_metadata,
    classify_packet_trust_label,
    render_packet_trust_metadata_markdown,
)
from .source_registry import (
    get_source_policy,
    list_sources_by_trust_state,
    load_source_registry,
    validate_source_registry,
)

__all__ = [
    "FLAG_PHRASES",
    "build_packet_trust_metadata",
    "classify_packet_trust_label",
    "default_source_state",
    "get_source_policy",
    "list_sources_by_trust_state",
    "load_source_registry",
    "quarantine_decision",
    "render_packet_trust_metadata_markdown",
    "scan",
    "validate_source_registry",
]
