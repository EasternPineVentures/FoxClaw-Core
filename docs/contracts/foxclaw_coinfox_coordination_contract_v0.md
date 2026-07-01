# FoxClaw-CoinFox Coordination Contract V0

Last updated: 2026-07-01.

Status: docs, schema, fixtures, and demo only. No production behavior is wired in this pass.

## Purpose

FoxClaw and CoinFox need to coordinate without reading each other's internals.

This contract gives them a small state machine:

```text
IntentPacket
  -> CoordinationDecision(ack)
  -> ActionReceipt(executed)
  -> OutcomeReceipt

IntentPacket
  -> CoordinationDecision(block)
  -> ActionReceipt(blocked)
```

The goal is not autonomy by vibes. The goal is explicit intent, explicit approval or block,
and receipt-backed history before either system acts.

## System Boundaries

FoxClaw is the core decision and evidence engine. It watches sources, compares evidence,
summarizes context, stores internal receipts, and keeps private evidence private.

FoxClaw Ledger is the proof and history layer. In V0 demo mode it is a chronological JSON
list. Later it can become a durable append-only store.

CoinFox is the public community and market discussion layer. It can receive public-safe
summaries, draft cards, public receipt references, and source links. It returns public
engagement receipts such as comments, challenges, saves, and votes.

CoinFox is paper-only public market discussion. It does not place orders, route orders,
hold funds, provide financial advice, or provide real lending.

## State Machine Rules

1. No action without an `IntentPacket`.
2. No action proceeds without a `CoordinationDecision` of `ack`.
3. Every action or block produces an `ActionReceipt`.
4. Important actions later receive an `OutcomeReceipt`.
5. Every packet includes `classification`, `authority_requested`, `authority_granted`,
   and `packet_hash`.
6. Private evidence must not be exported to CoinFox.
7. CoinFox can receive public-safe summaries, draft cards, and public receipt references.
8. CoinFox returns public engagement receipts: comments, challenges, saves, and votes.

## Packet Types

### IntentPacket

Direction: FoxClaw -> CoinFox.

Purpose: FoxClaw states what it intends to do before doing it.

Required concepts:

- requested action
- why now
- expected output
- public-safe summary
- classification
- authority requested
- authority granted, usually empty at intent time
- private evidence export flag, always false
- expiration time

Example V0 allowed intent:

```text
requested_action = prepare_draft_cards
authority_requested = ["draft_only"]
authority_granted = []
```

### CoordinationDecision

Direction: CoinFox -> FoxClaw.

Purpose: CoinFox acknowledges or blocks the intent before FoxClaw acts.

Valid decisions:

- `ack`
- `block`

An `ack` may grant only the authority needed for the next safe step, such as `draft_only`.
A `block` grants no authority and must include the reason.

### ActionReceipt

Direction: FoxClaw -> CoinFox.

Purpose: FoxClaw records what happened after the decision.

The receipt must exist whether the action executed or was blocked.

Valid statuses:

- `executed`
- `blocked`

Example V0 executed action:

```text
action_taken = exported_sanitized_cards
authority_granted = ["draft_only"]
```

### OutcomeReceipt

Direction: CoinFox -> FoxClaw.

Purpose: CoinFox returns public engagement results after the public or draft surface is
reviewed.

The V0 engagement receipt carries:

- comments count
- challenges count
- saves count
- votes count
- public links or public receipt references
- outcome summary
- follow-up questions for FoxClaw

## Allowed Actions

| Action | Allowed in V0 | Notes |
| --- | --- | --- |
| `prepare_draft_cards` | yes | FoxClaw may prepare public-safe draft cards. |
| `export_sanitized_cards` | yes, after ack | Only sanitized cards and public receipt references. |
| `return_engagement_receipt` | yes | CoinFox may return public engagement aggregates. |
| `request_revision` | yes | CoinFox may ask FoxClaw to revise or narrow a packet. |

## Blocked Actions

| Action or authority | Blocked in V0 | Reason |
| --- | --- | --- |
| `auto_publish` | yes | CoinFox owns publication and human/product gates. |
| `place_order` | yes | No trading authority. |
| `route_order` | yes | No brokerage or execution path. |
| `hold_funds` | yes | No custody. |
| `provide_financial_advice` | yes | Public discussion only, not individualized advice. |
| `real_lending` | yes | CoinFox has no real lending authority. |
| private evidence export | yes | FoxClaw internals and raw private evidence stay private. |

The schema intentionally allows an `auto_publish` request so a packet can record the
attempt. The semantic policy must block it.

## Safety Rules

```text
can_submit_order = false
can_move_funds = false
live_execution_allowed = false
can_publish_to_coinfox = false
can_export_private_evidence = false
not_financial_advice = true
paper_only = true
```

No trading. No custody. No private evidence export. No auto-publishing. No real lending.
No financial advice.

## Future Integration Notes

V0 is file/demo only. Future work should add:

- durable append-only FoxClaw Ledger storage
- packet hash verification against the previous packet
- CoinFox-side schema copy and import guard
- API endpoint or file-drop exchange after auth boundaries exist
- public engagement receipt ingestion into FoxClaw outcome memory
- human review gates before any production CoinFox publish path

Do not wire this contract into production behavior until both repos have compatible tests
and a reviewed trust boundary.
