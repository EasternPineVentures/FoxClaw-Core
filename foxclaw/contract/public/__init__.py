"""Public FoxClaw contract schema resources.

This package is still a contract scaffold. It exposes schema file names and paths,
not decision logic or write authority.
"""
from __future__ import annotations

from pathlib import Path

PUBLIC_CONTRACT_DIR = Path(__file__).resolve().parent

SCHEMA_FILES = (
    "public_intelligence_card.schema.json",
    "public_scorecard.schema.json",
    "attention_receipt.schema.json",
    "risk_classification.schema.json",
)

__all__ = ["PUBLIC_CONTRACT_DIR", "SCHEMA_FILES", "schema_path"]


def schema_path(name: str) -> Path:
    """Return a public schema path by known schema file name."""
    if name not in SCHEMA_FILES:
        raise ValueError(f"unknown public contract schema: {name}")
    return PUBLIC_CONTRACT_DIR / name
