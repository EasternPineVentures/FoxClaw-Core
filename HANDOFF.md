# HANDOFF - foxclaw-core

This file is the operational passoff for the clean FoxClaw company repo.
Read it before changing code, then verify with `git log --oneline -10` and the tests.

Last updated: 2026-06-18
Branch: `master`
Version: `0.2.2`
Working repo: `C:\Users\brend\dev\foxclaw-core`

## Current Lane

Forecast Desk / Kalshi-first event-contract intelligence is the active lane.

FoxClaw is a decision matrix first. Kalshi is one public-data adapter feeding the
receipt-driven decision machinery. The core `engine/` must remain domain-neutral; market
and venue language stays under `foxclaw/adapters/`.

Company posture:

- This repo is the clean migration target and public-ready work surface.
- Git is the handoff path.
- OneDrive is not an authoritative runtime or database source.
- The old OneDrive FoxClaw checkout is reference-only unless a task explicitly says
  otherwise.
- No credentials, DB files, raw runtime logs, or private keys belong in git.

## Phase Progress

Done before this pass:

- `v0.2.0` engine phase: neutral edge, score, gate, tier owner, and market scoreboard
  adapter were wired end to end.
- Forecast Desk P10 Phase 0: event-contract scaffold, hard read-only/paper-only locks,
  venue metadata, eligibility denial, and pricing doctrine in code.

Done in this pass:

- Phase A read-only Kalshi API Desk implemented.
- Public REST environment metadata added for production and demo.
- Credential-free REST transport added with central 429 backoff.
- Cursor paginator added with repeated-cursor rejection and max page/item guards.
- Kalshi fixed-point parsing uses `Decimal` and rejects binary float money.
- Normalized series, event, market, and order-book contracts added.
- YES/NO bid-only order books reconstruct asks via complementarity.
- Crossed or empty books become non-tradeable receipts rather than fake executable books.
- Historical cutoff parsing and deterministic live/historical market merge helpers added.
- `tools/kalshi_api_desk.py` added with offline fixture mode and read-only commands:
  `doctor`, `series`, `events`, `markets`, `inspect`, `orderbook`, `trades`.
- `docs/kalshi_api_field_guide.md` added.
- Offline Kalshi fixtures and tests added.
- Phase B Forecast Desk snapshot ledger implemented.
- `foxclaw/adapters/event_contracts/storage/` added with Forecast DB resolution, cloud-sync
  path rejection, idempotent schema initialization, repository writes, raw-hash lineage,
  sync cursors, and gzip JSONL raw archive helpers.
- `tools/forecast_desk_sync.py` added for one-shot fixture/live read-only sync.
- `tools/freeze_forecast_db_schema.py`, `config/forecast_db_schema.frozen.json`, and
  `docs/forecast_db_schema.md` added as the schema freeze contract.
- `.gitignore` corrected from `storage/` to `/storage/` so source packages named storage are
  not hidden.
- Phase B regression tests added for schema idempotence, raw archive round-trip,
  normalized-row-to-raw lineage, no-duplicate fixture sync resume, frozen schema verification,
  and OneDrive DB path rejection.

## Hard Rails

These remain non-negotiable:

```text
CAN_SUBMIT_ORDER = false
CAN_MOVE_FUNDS = false
LIVE_EXECUTION_ALLOWED = false
DEFAULT_AUTHORITY_LEVEL = A4_prohibited
```

No live order path, no account creation, no funds movement, no production credential load,
no jurisdiction bypass, and no LLM authority path. Public information only.

## Verification

Baseline before edits:

```text
python -m pytest -q        -> 117 passed
python tools/check_invariants.py -> green
git diff --check           -> green
```

Focused Phase A check before handoff update:

```text
python -m pytest tests\unit\test_event_contract_models.py tests\unit\test_kalshi_normalization.py tests\unit\test_kalshi_orderbook.py tests\unit\test_kalshi_pagination.py tests\regression\test_kalshi_api_desk.py -q
-> 19 passed
```

Phase-boundary result:

```text
python -m pytest -q        -> 136 passed
python tools/check_invariants.py -> green
git diff --check           -> green
```

Focused Phase B check before handoff update:

```text
python -m pytest tests\regression\test_forecast_storage_lineage.py tests\regression\test_forecast_db_schema_frozen.py -q
-> 7 passed
python tools\freeze_forecast_db_schema.py --check -> green
fixture sync -> 1 series, 1 event, 1 market, 1 orderbook, 4 raw payload rows
```

Phase B full-suite result:

```text
python -m pytest -q        -> 143 passed
python tools/check_invariants.py -> green
git diff --check           -> green
```

## Next Phase

Continue to Phase C after Phase B is committed cleanly:

```powershell
python -m pytest -q
python tools\check_invariants.py
git diff --check
git add .
git commit -m "Add Forecast Desk snapshot ledger and schema guard"
```

Then implement the dossier and resolution pipeline:

```text
foxclaw/adapters/event_contracts/dossiers.py
foxclaw/adapters/event_contracts/resolution.py
foxclaw/adapters/event_contracts/policy.py
foxclaw/adapters/event_contracts/contracts.py
docs/forecast_receipt_contract.md
docs/data_retention_and_privacy.md
```

## Watch

- Keep `engine/` free of Kalshi/event-contract vocabulary.
- Keep default tests offline and deterministic.
- Do not hardcode `C:\Users\brend\...` in code; use explicit args, environment variables,
  then repo-local fallback.
- Do not put Forecast Desk DBs under OneDrive.
- Treat Kalshi docs as live; changelog drift must become a later receipt watcher.
