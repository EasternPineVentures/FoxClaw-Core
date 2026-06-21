# Discord Parser Port Plan

Status: planning contract foundation.
Machine identity: A1.
Source repo path: C:\Users\brend\dev\foxclaw-core.
Branch: planning/parser-compatibility-v0.
Anchor commit: 85deb62d7e11f3d440c87eed37e7df88379b5996.

## Scope

This plan defines the v2 parser migration boundary. It does not connect
Discord, read private Discord messages, publish to CoinFox, or change execution
authority. A2's read-only runtime inventory now identifies the active parser
surface that v2 must match offline.

## A2 Verified Runtime Facts

| Runtime surface | Verified fact |
| --- | --- |
| Live listener | `trading/app/user_ingest.py` |
| Credential | `NORMAL_USER_TOKEN` via `USER_TOKEN` |
| Credential classification | `REPLACE_URGENT` / `DO_NOT_PORT` / `DO_NOT_EXPAND` |
| Live parser wrapper | `tools/raw_parser.py` |
| Parser version | `live_raw_parser_admission_v13` |
| Parser implementation | `src/parsers/signal_parser.py::parse_trade_signal` |
| Parser kind | deterministic rule-based parser, not LLM-backed |
| Source filtering | watched channels plus watched parent threads |
| Dedup key | normalized content hash plus `source_id`; message id is lineage only |
| Raw write table | `raw_events` |
| Parse write table | `parse_attempts` |
| Promotion tool | `tools/promote_accepted_candidates.py` |
| Downstream authority | paper-only |
| Rejection behavior | explicit rejection reasons must be preserved |

## Target Flow

```text
Discord transport event or replay fixture
-> RawSourceEvent
-> ParseAttempt
-> AcceptedCandidate or ParserRejection
-> existing claim/evidence/readiness/publication contracts
```

## Ownership

| Layer | Owner | Purpose |
| --- | --- | --- |
| Discord transport | `foxclaw/adapters/discord/` | Normalize Discord envelopes, edits, deletes, source metadata, and replay inputs. No trading decisions. |
| Market-signal normalization | `foxclaw/adapters/market/` | Normalize symbol, direction, entry, stop, target, time horizon, and market-specific payload shape. |
| Neutral replay/provenance | `foxclaw/contract/internal/` and store lineage | Preserve RawSourceEvent, ParseAttempt, AcceptedCandidate, and ParserRejection receipts. |
| Admission policy | `foxclaw/policy/` | Decide whether a parse attempt may become an accepted candidate. No execution authority. |
| Persistence | `foxclaw/store/` | Use current RawEventStore, ParseAttemptStore, and AcceptedCandidateStore. Do not add a duplicate persistence layer without review. |
| Public handoff | `foxclaw/contract/public/` and `foxclaw/intelligence/staging.py` | Only publication-approved, Contract 1.0.0-valid derivatives may stage. |

## Stable Internal Contracts

RawSourceEvent carries the opaque source event, timestamps, content hash,
synthetic flag, deduplication metadata, payload classification, private/public
state, quarantine, and lineage. For Discord compatibility, the dedupe key is
derived from normalized content plus source id; message id stays private
lineage and must not become the dedupe key.

ParseAttempt carries parser identity, mode, created timestamp, accepted boolean,
status, reason codes, normalized structured payload, rejection reason, error
class, confidence, provider/model metadata, and lineage.

AcceptedCandidate carries the admitted candidate identity, event and attempt
references, source reference, parser version, candidate type, normalized payload,
confidence, admission policy, admission reason, evidence hash, status,
timestamp, and lineage.

ParserRejection carries rejected event and attempt references, reason code, safe
diagnostic category, retryability, parser identity, timestamp, safe diagnostic,
and lineage.

## Remaining Runtime Unknowns

- whether multiple `user_ingest.py` processes are duplicate gateway listeners;
- exact operator-approved private replay corpus path.

## Non-Goals

- No new live Discord listener.
- No normal user-token port.
- No parser redesign.
- No CoinFox API, DB, webhook, or publishing.
- No raw Discord content in committed fixtures.
- No live order, fund, wallet, or execution path.

## Next Gate

Do not implement the v2 compatibility parser until A2 has delivered the legacy
runtime inventory and sanitized replay evidence.
