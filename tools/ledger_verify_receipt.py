#!/usr/bin/env python3
"""Verify local FoxClaw Ledger V0 receipt payload hashes."""

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
    parser.add_argument("--receipt-id", help="verify one receipt id")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args(argv)

    store = ReceiptStore(args.store)
    results = store.verify(args.receipt_id)
    payload = {
        "schema_version": "foxclaw_ledger_verify.v0",
        "receipt_store": str(store.path),
        "checked": len(results),
        "valid": all(item["valid"] for item in results),
        "results": results,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_markdown(payload))
    return 0 if payload["valid"] else 1


def _render_markdown(payload: dict) -> str:
    lines = [
        "# FoxClaw Ledger Verify",
        "",
        f"Store: `{payload['receipt_store']}`",
        f"Checked: `{payload['checked']}`",
        f"Valid: `{str(payload['valid']).lower()}`",
        "",
    ]
    for item in payload["results"]:
        lines.append(f"- `{item['receipt_id']}` valid=`{str(item['valid']).lower()}`")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
