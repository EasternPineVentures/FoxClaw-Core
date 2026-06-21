# A1 Parser Contract Foundation Handoff

Status: planning branch handoff.
Machine identity: A1.
UTC timestamp: 2026-06-20T03:59:19Z.
Source repo path: C:\Users\brend\dev\foxclaw-core.
Branch: planning/parser-compatibility-v0.
Anchor commit: 85deb62d7e11f3d440c87eed37e7df88379b5996.
Tool: Codex.

## Scope

This pass defines parser compatibility contracts, fixture rules, auth cutover
doctrine, and parity measurement. It does not port parser code, connect Discord,
read private messages, change Microscope, modify CoinFox, publish staged cards,
or update shared release metadata.

## Contract Versions

```text
internal.raw_source_event.v1
internal.parse_attempt.v1
internal.accepted_candidate.v1
internal.parser_rejection.v1
```

## Unknowns Awaiting A2

Resolved by A2 runtime inventory:

- live listener: `trading/app/user_ingest.py`;
- credential: `NORMAL_USER_TOKEN` via `USER_TOKEN`, classified
  `REPLACE_URGENT` / `DO_NOT_PORT` / `DO_NOT_EXPAND`;
- parser wrapper: `tools/raw_parser.py`;
- parser implementation:
  `src/parsers/signal_parser.py::parse_trade_signal`;
- parser version: `live_raw_parser_admission_v13`;
- parser kind: deterministic/rule-based, not LLM-backed;
- dedup key: normalized content hash plus `source_id`; message id is lineage
  only;
- source filtering: watched channels plus watched parent threads;
- writes: `raw_events` and `parse_attempts`;
- promotion: `tools/promote_accepted_candidates.py`;
- downstream: paper-only;
- explicit rejection reasons must be preserved.

Remaining runtime unknowns:

- whether multiple `user_ingest.py` processes are duplicate gateway listeners;
- exact operator-approved private replay corpus path.

## A2 Inputs Needed Before Implementation

- operator-approved private replay corpus path;
- duplicate listener/process interpretation;
- sanitized parser fixture corpus;
- accepted/rejected distribution;
- duplicate disposition evidence;
- edited/deleted message evidence where present.

## Stop Line

A1 may implement the offline v13 compatibility parser after this reconciliation.
It must not connect Discord, port `USER_TOKEN`, write live DB rows, publish to
CoinFox, or grant execution authority.
