# FoxClaw Ledger V0

Last updated: 2026-07-01.

Status: local-only receipt storage and review queue. No live CoinFox API calls are wired.

## Purpose

FoxClaw Ledger V0 is the receipt, proof, and history layer for the
FoxClaw-CoinFox Coordination Contract V0.

It records what each coordination packet meant in FoxClaw terms:

```text
IntentPacket -> coordination_intent receipt
CoordinationDecision -> coordination_decision receipt
ActionReceipt -> coordination_action_receipt
OutcomeReceipt -> coordination_outcome_receipt + optional review task
```

The Ledger does not decide truth and does not publish. It preserves the evidence of what
was requested, granted, blocked, executed, and returned for later review.

## What Ledger Stores

Each receipt includes:

- `receipt_id`
- `receipt_type`
- `source_system`
- `target_system`
- `packet_type`
- `packet_id`
- `intent_id`
- `classification`
- `authority_requested`
- `authority_granted`
- `status`
- `artifact_refs`
- `input_hash`
- `output_hash`
- `payload_hash`
- `created_at`
- `review_after`
- `review_status`

V0 stores receipts as JSONL:

```text
runtime_logs/foxclaw_ledger/receipts.jsonl
```

Review tasks are also JSONL:

```text
runtime_logs/foxclaw_ledger/review_tasks.jsonl
```

`runtime_logs/` is local runtime state and is not committed.

## What Ledger Must Not Store

FoxClaw Ledger V0 must not store:

- API keys
- access tokens
- passwords
- private keys
- seed phrases
- wallet addresses
- private evidence text
- private Discord text
- account data
- raw CoinFox internals

It preserves classification and authority fields, but it does not export private evidence.

## Relation To FCDB

FCDB is the technical database layer. It can hold operational tables, state, and future
database-backed stores.

FoxClaw Ledger is the proof/history layer. V0 uses JSONL deliberately because the first job
is to make the receipt chain simple, inspectable, append-only, and easy to test. Later, FCDB
can host an indexed ledger mirror after the JSONL contract is stable.

## Relation To CoinFox

CoinFox is the public community and social market layer. It can receive public-safe draft
cards and public receipt references. It returns public engagement receipt data: comments,
challenges, saves, and votes.

CoinFox remains paper-only public market discussion. It does not place orders, route orders,
hold funds, provide individualized financial advice, or provide real lending.

## Relation To Coordination Contract

The Coordination Contract defines the packet language.

FoxClaw Ledger records the receipt history produced from those packets.

The key boundary is:

```text
FoxClaw and CoinFox coordinate through public contract packets,
not direct database access or hidden internal coupling.
```

## Safety Boundaries

```text
can_submit_order=false
can_move_funds=false
live_execution_allowed=false
can_publish_to_coinfox=false
can_export_private_evidence=false
can_call_live_coinfox_api=false
can_provide_financial_advice=false
can_real_lending=false
```

Blocked requests such as `auto_publish` are recorded as blocked receipts. They are not
executed.

## Operator Commands

Record the demo packet flow into the local ledger:

```powershell
python tools\ledger_record_demo.py
```

List receipts:

```powershell
python tools\ledger_list_receipts.py
python tools\ledger_list_receipts.py --json
```

Verify receipt hashes:

```powershell
python tools\ledger_verify_receipt.py
python tools\ledger_verify_receipt.py --json
```

List review tasks:

```powershell
python tools\ledger_review_queue.py
python tools\ledger_review_queue.py --json
```

Use temporary paths for tests or rehearsals:

```powershell
python tools\ledger_record_demo.py --store .\runtime_logs\foxclaw_ledger\demo_receipts.jsonl --review-queue .\runtime_logs\foxclaw_ledger\demo_review_tasks.jsonl
```

## Future Integration Notes

Future passes can add:

- FCDB-backed ledger indexing
- previous-hash chain verification across JSONL rows
- signed receipt batches
- CoinFox-side fixture import tests
- operator review workflow for pending review tasks

Do not connect live CoinFox APIs until both repos have compatible contract tests and a
reviewed auth boundary.
