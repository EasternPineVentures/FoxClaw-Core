# Discord Auth Cutover Plan

Status: planning contract foundation.
Machine identity: A1.
Source repo path: C:\Users\brend\dev\foxclaw-core.
Branch: planning/parser-compatibility-v0.
Anchor commit: 85deb62d7e11f3d440c87eed37e7df88379b5996.

## Target Architecture

The v2 target is bot-token only.

```text
NORMAL_USER_TOKEN = REPLACE_URGENT, DO_NOT_PORT, DO_NOT_EXPAND
USER_TOKEN = legacy v1 environment variable, DO_NOT_PORT
```

No normal user token, self-bot behavior, OAuth user-token scraping, or credential
workaround may be ported into FoxClaw Core.

A2 verified that the legacy runtime uses `NORMAL_USER_TOKEN` through the
`USER_TOKEN` environment variable. This is a cutover liability, not a migration
dependency.

## Required Cutover Properties

- one live Discord listener at a time;
- least-privilege Discord intents;
- local secret storage only;
- no credential values in source, logs, command lines, fixtures, reports, or
  chat;
- credential rotation before cutover if v1 used a normal user token;
- replay and parity must work without Discord availability;
- rollback keeps v1 as the only live listener until v2 is explicitly approved.

## Credential Reporting

A2 may report only:

```text
credential_type
environment_variable_name
secret_storage_location_class
rotation_required
```

A2 must not report token values or token fragments.

## Cutover Ladder

1. A2 completed read-only runtime inventory.
2. A2 freezes sanitized v1 replay evidence.
3. A1 implements offline compatibility parser.
4. Independent security review approves private shadow.
5. A2 runs shadow parity against captured messages.
6. A1 integrates only after parity approval.
7. A1 proves controlled private staging.
8. A later, separate cutover plan decides whether v2 becomes the live listener.

## Rollback

Rollback means v1 remains or returns as the only live listener. V2 replay and
shadow tools must be offline-only and must not hold credentials required to
continue processing captured fixtures.

## Remaining Runtime Unknowns

- whether multiple `user_ingest.py` processes are duplicate gateway listeners;
- exact operator-approved private replay corpus path.
