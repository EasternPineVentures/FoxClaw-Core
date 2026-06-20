# Discord Parser Port Plan

Status: planning contract foundation.
Machine identity: A1.
Source repo path: C:\Users\brend\dev\foxclaw-core.
Branch: planning/parser-compatibility-v0.
Anchor commit: 85deb62d7e11f3d440c87eed37e7df88379b5996.

## Scope

This plan defines the v2 parser migration boundary. It does not port the
legacy parser, connect Discord, read private Discord messages, publish to
CoinFox, or change execution authority.

A2 owns the legacy runtime inventory. Any behavior not proven by A2 remains:

```text
UNKNOWN_PENDING_A2_INVENTORY
```

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
state, quarantine, and lineage.

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

## Unknowns Awaiting A2

- Live listener entrypoint.
- Active parser function/class.
- Discord credential type and environment variable name.
- Source/channel filter semantics.
- Duplicate processing key.
- Provider/model, timeout, retry, and fallback chain.
- Edited/deleted message behavior.
- Which parse failures are explicit versus swallowed.
- Candidate promotion trigger.
- Exact v1 normalized payload semantics.

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
