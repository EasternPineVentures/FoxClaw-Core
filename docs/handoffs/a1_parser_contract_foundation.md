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

```text
UNKNOWN_PENDING_A2_INVENTORY
```

This marker is intentional for:

- live listener entrypoint;
- parser entrypoint;
- credential type and environment variable;
- source/channel filter semantics;
- duplicate key and reconnect behavior;
- provider/model, timeout, retry, and fallback chain;
- exact v1 normalized payload semantics;
- required parity sample size and acceptable mismatch rate.

## A2 Inputs Needed Before Implementation

- legacy runtime inventory;
- component manifest;
- sanitized parser fixture corpus;
- parser-version distribution;
- accepted/rejected distribution;
- duplicate disposition evidence;
- provider failure evidence;
- edited/deleted message evidence where present.

## Stop Line

A1 should not implement the v2 compatibility parser until A2 evidence is
reviewed and reconciled.
