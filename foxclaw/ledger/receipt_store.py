"""Local JSONL store for FoxClaw Ledger V0 receipts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from foxclaw.ledger.receipt_hashing import canonical_json, verify_receipt_hash

REPO = Path(__file__).resolve().parents[2]
DEFAULT_RECEIPT_STORE_PATH = REPO / "runtime_logs" / "foxclaw_ledger" / "receipts.jsonl"

SECRET_KEY_FRAGMENTS = (
    "api_key",
    "access_token",
    "auth_token",
    "authorization",
    "client_secret",
    "mnemonic",
    "password",
    "private_key",
    "secret_key",
    "seed_phrase",
    "wallet_address",
)
SECRET_VALUE_FRAGMENTS = ("sk-", "xoxb-", "ghp_", "secret_", "api_key=")


class ReceiptStore:
    def __init__(self, path: str | Path = DEFAULT_RECEIPT_STORE_PATH) -> None:
        self.path = Path(path)

    def append(self, receipt: dict[str, Any]) -> dict[str, Any]:
        _assert_safe_to_store(receipt)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(receipt) + "\n")
        return receipt

    def list_receipts(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        receipts: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                receipts.append(json.loads(line))
        return receipts

    def get_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        for receipt in self.list_receipts():
            if receipt.get("receipt_id") == receipt_id:
                return receipt
        return None

    def verify(self, receipt_id: str | None = None) -> list[dict[str, Any]]:
        receipts = self.list_receipts()
        if receipt_id is not None:
            receipts = [receipt for receipt in receipts if receipt.get("receipt_id") == receipt_id]
        return [
            {
                "receipt_id": receipt.get("receipt_id"),
                "valid": verify_receipt_hash(receipt),
                "packet_type": receipt.get("packet_type"),
                "status": receipt.get("status"),
            }
            for receipt in receipts
        ]


def _assert_safe_to_store(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in SECRET_KEY_FRAGMENTS):
                raise ValueError(f"{path}.{key}: secret-like key cannot be stored")
            if lowered == "private_evidence_refs" and child:
                raise ValueError(f"{path}.{key}: private evidence refs cannot be stored")
            _assert_safe_to_store(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_safe_to_store(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in SECRET_VALUE_FRAGMENTS):
            raise ValueError(f"{path}: secret-like value cannot be stored")
