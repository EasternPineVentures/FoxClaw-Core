"""FoxClaw Ledger V0 local outcome review queue."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from foxclaw.ledger.receipt_hashing import canonical_json
from foxclaw.ledger.receipt_store import _assert_safe_to_store

REPO = Path(__file__).resolve().parents[2]
DEFAULT_REVIEW_QUEUE_PATH = REPO / "runtime_logs" / "foxclaw_ledger" / "review_tasks.jsonl"


@dataclass(frozen=True)
class ReviewTask:
    task_id: str
    linked_intent_id: str
    linked_receipt_id: str
    reason: str
    status: str
    created_at: str
    review_after: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReviewQueue:
    def __init__(self, path: str | Path = DEFAULT_REVIEW_QUEUE_PATH) -> None:
        self.path = Path(path)

    def append(self, task: dict[str, Any]) -> dict[str, Any]:
        _assert_safe_to_store(task)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(task) + "\n")
        return task

    def list_tasks(self, *, status: str | None = None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        tasks = [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if status is not None:
            tasks = [task for task in tasks if task.get("status") == status]
        return tasks

    def create_from_receipt(self, receipt: dict[str, Any], *, reason: str | None = None) -> dict[str, Any] | None:
        task = review_task_from_receipt(receipt, reason=reason)
        if task is None:
            return None
        return self.append(task.to_dict())


def review_task_from_receipt(receipt: dict[str, Any], *, reason: str | None = None) -> ReviewTask | None:
    if receipt.get("packet_type") != "OutcomeReceipt":
        return None
    if receipt.get("review_status") != "pending" and not receipt.get("review_after"):
        return None
    resolved_reason = reason or "OutcomeReceipt requested FoxClaw review."
    material = {
        "linked_receipt_id": receipt["receipt_id"],
        "linked_intent_id": receipt["intent_id"],
        "reason": resolved_reason,
    }
    task_id = "fcreview-" + hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()[:16]
    return ReviewTask(
        task_id=task_id,
        linked_intent_id=str(receipt["intent_id"]),
        linked_receipt_id=str(receipt["receipt_id"]),
        reason=resolved_reason,
        status="pending",
        created_at=str(receipt["created_at"]),
        review_after=receipt.get("review_after"),
    )
