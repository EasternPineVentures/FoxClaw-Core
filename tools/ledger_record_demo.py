#!/usr/bin/env python3
"""Record the coordination demo packets into the local FoxClaw Ledger V0 JSONL store."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.contract.public.coinfox_coordination import build_demo_ledger  # noqa: E402
from foxclaw.ledger import DEFAULT_RECEIPT_STORE_PATH, DEFAULT_REVIEW_QUEUE_PATH  # noqa: E402
from foxclaw.ledger.receipt_models import receipt_from_coordination_packet  # noqa: E402
from foxclaw.ledger.receipt_store import ReceiptStore  # noqa: E402
from foxclaw.ledger.review_queue import ReviewQueue  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=str(DEFAULT_RECEIPT_STORE_PATH), help="receipt JSONL path")
    parser.add_argument(
        "--review-queue",
        default=str(DEFAULT_REVIEW_QUEUE_PATH),
        help="review-task JSONL path",
    )
    args = parser.parse_args(argv)

    ledger = build_demo_ledger()
    store = ReceiptStore(args.store)
    review_queue = ReviewQueue(args.review_queue)
    written_receipts = []
    written_tasks = []
    for packet in ledger["packets"]:
        receipt = receipt_from_coordination_packet(packet).to_dict()
        store.append(receipt)
        written_receipts.append(receipt["receipt_id"])
        task = review_queue.create_from_receipt(receipt)
        if task:
            written_tasks.append(task["task_id"])

    print(
        json.dumps(
            {
                "schema_version": "foxclaw_ledger_record_demo.v0",
                "receipt_store": str(store.path),
                "review_queue": str(review_queue.path),
                "receipts_written": len(written_receipts),
                "review_tasks_written": len(written_tasks),
                "receipt_ids": written_receipts,
                "review_task_ids": written_tasks,
                "live_api_calls": False,
                "production_writes": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
