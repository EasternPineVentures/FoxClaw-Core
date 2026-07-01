"""Public FoxClaw contract schema resources."""
from __future__ import annotations

import json
from pathlib import Path

PUBLIC_CONTRACT_DIR = Path(__file__).resolve().parent
PUBLIC_CONTRACT_VERSION = "1.0.0"

SCHEMA_FILES = (
    "public_intelligence_card.schema.json",
    "public_scorecard.schema.json",
    "attention_receipt.schema.json",
    "coinfox_curated_packet.schema.json",
    "risk_classification.schema.json",
    "verified_outcome.schema.json",
)

__all__ = [
    "PUBLIC_CONTRACT_DIR",
    "PUBLIC_CONTRACT_VERSION",
    "SCHEMA_FILES",
    "manifest",
    "schema_path",
]


def schema_path(name: str) -> Path:
    """Return a public schema path by known schema file name."""
    if name not in SCHEMA_FILES:
        raise ValueError(f"unknown public contract schema: {name}")
    return PUBLIC_CONTRACT_DIR / name


def manifest() -> dict[str, object]:
    """Load the frozen public contract manifest."""
    return json.loads((PUBLIC_CONTRACT_DIR / "manifest.json").read_text(encoding="utf-8"))
