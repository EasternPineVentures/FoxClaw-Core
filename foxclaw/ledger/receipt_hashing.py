"""Stable hashing helpers for FoxClaw Ledger receipts."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Mapping


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Return deterministic JSON for hashing and durable receipt comparison."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def receipt_payload_hash(receipt: Mapping[str, Any]) -> str:
    """Hash a receipt with its ``payload_hash`` field blanked to avoid recursion."""
    payload = deepcopy(dict(receipt))
    payload["payload_hash"] = ""
    return "sha256:" + hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def verify_receipt_hash(receipt: Mapping[str, Any]) -> bool:
    """Return true when the stored payload hash matches the receipt body."""
    stored_hash = receipt.get("payload_hash")
    if not isinstance(stored_hash, str) or not stored_hash.startswith("sha256:"):
        return False
    return stored_hash == receipt_payload_hash(receipt)
