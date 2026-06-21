"""Internal FoxClaw contract schema resources.

Internal contracts can contain private references, diagnostics, quarantine state,
and provider metadata. They are not public CoinFox payloads.
"""
from __future__ import annotations

from pathlib import Path

INTERNAL_CONTRACT_DIR = Path(__file__).resolve().parent

SCHEMA_FILES = (
    "raw_source_event.schema.json",
    "parse_attempt.schema.json",
    "accepted_candidate.schema.json",
    "parser_rejection.schema.json",
    "parser_legacy_result.schema.json",
    "parser_parity_report.schema.json",
    "claim_packet.schema.json",
    "evidence_bundle.schema.json",
    "attention_aggregate.schema.json",
    "tradeability_snapshot.schema.json",
    "trade_readiness_verdict.schema.json",
    "publication_decision.schema.json",
    "verified_outcome.schema.json",
)

__all__ = ["INTERNAL_CONTRACT_DIR", "SCHEMA_FILES", "schema_path"]


def schema_path(name: str) -> Path:
    """Return an internal schema path by known schema file name."""
    if name not in SCHEMA_FILES:
        raise ValueError(f"unknown internal contract schema: {name}")
    return INTERNAL_CONTRACT_DIR / name
