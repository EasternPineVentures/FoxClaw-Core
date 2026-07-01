#!/usr/bin/env python3
"""List local FoxClaw Ledger V0 receipts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from foxclaw.ledger import DEFAULT_RECEIPT_STORE_PATH  # noqa: E402
from foxclaw.ledger.receipt_store import ReceiptStore  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=str(DEFAULT_RECEIPT_STORE_PATH), help="receipt JSONL path")
    parser.add_argument("--limit", type=int, default=20, help="maximum receipts to print")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args(argv)

    store = ReceiptStore(args.store)
    receipts = store.list_receipts()[-args.limit :]
    payload = {
        "schema_version": "foxclaw_ledger_receipt_list.v0",
        "receipt_store": str(store.path),
        "receipt_count": len(receipts),
        "receipts": receipts,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_markdown(payload))
    return 0


def _render_markdown(payload: dict) -> str:
    lines = [
        "# FoxClaw Ledger Receipts",
        "",
        f"Store: `{payload['receipt_store']}`",
        f"Receipts shown: `{payload['receipt_count']}`",
        "",
    ]
    for receipt in payload["receipts"]:
        lines.append(
            f"- `{receipt['receipt_id']}` {receipt['packet_type']} "
            f"{receipt['source_system']}->{receipt['target_system']} status=`{receipt['status']}`"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
