# A2 Parser Parity Contract Package

Status: A1 contract package for A2 legacy replay.
Machine identity: A1.
Source repo path: C:\Users\brend\dev\foxclaw-core.
Branch: feature/parser-compat-v0.

## Scope

This package gives A2 a schema-valid way to export legacy parser behavior from
its private replay corpus. It does not connect Discord, run live parser work,
touch CoinFox, alter Microscope, write live DB rows, or change execution
authority.

## Confirmed A2 Runtime State

- one actual listener remains;
- canonical listener PID `13624`;
- duplicate listener PID `3464` stopped;
- `raw_events` continued advancing;
- no respawn detected;
- no token or env exposure.

## Schemas

```text
foxclaw/contract/internal/parser_legacy_result.schema.json
foxclaw/contract/internal/parser_parity_report.schema.json
```

`parser_legacy_result.v1` is the JSONL line contract A2 should emit. It records
the legacy v13 parse result, source-scoped dedupe lineage, parser identity, and
explicit safety flags. It must not include raw message body, Discord ids,
Discord links, token values, CoinFox side effects, or live execution effects.

`parser_parity_report.v1` is the comparison report A1 emits when matching A2
legacy JSONL against v2 offline replay fixtures.

## A2 Validator Command

```powershell
python tools\validate_parser_legacy_results.py `
  --jsonl C:\path\to\legacy_parser_results.jsonl `
  --json
```

The validator returns `parser_legacy_validation.v1`. It reports line number,
field path, and code only. It does not print poisoned/private values.

## A1 Comparator Command

```powershell
python tools\compare_parser_parity.py `
  --legacy-jsonl C:\path\to\legacy_parser_results.jsonl `
  --fixtures-dir C:\path\to\sanitized_replay_fixtures `
  --json
```

The comparator returns `parser_parity_report.v1`. Required green shape:

```text
mismatch_count = 0
network = false
coinfox = false
execution_authority = false
writes = []
```

## JSONL Requirements For A2

Each line must be one `parser_legacy_result.v1` object with:

- `case_id` matching the sanitized replay fixture id A1 will run through v2;
- `foxclaw_core_target_commit` set to the A1 package commit;
- runtime state showing `single_listener_confirmed`;
- parser identity fixed to `live_raw_parser_admission_v13`;
- source filter semantics fixed to `watched_channels_and_parent_threads`;
- source dedupe as normalized content hash plus source id;
- message id treated as lineage only;
- accepted/rejected result;
- exact rejection reason;
- candidate type, symbol, side, entry, quantity, stop, and target when present;
- parser confidence as parser confidence only.

## Stop Lines

- Do not include raw Discord content.
- Do not include Discord ids, links, invites, source names, or token fragments.
- Do not expose `USER_TOKEN` or `NORMAL_USER_TOKEN` values.
- Do not run public staging, CoinFox writes, or execution paths.
- Do not treat parser confidence as edge, risk, or authority.
