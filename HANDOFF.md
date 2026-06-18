# HANDOFF - foxclaw-core

This file is the operational passoff for the clean FoxClaw company repo.
Read it before changing code, then verify with `git log --oneline -10` and the tests.

Last updated: 2026-06-18
Branch: `master`
Version: `0.3.1`
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
- Phase C dossier and resolution-quality pipeline implemented.
- `contracts.py`, `dossiers.py`, `resolution.py`, and `policy.py` now provide public-evidence
  eligibility verdicts, accepted evidence items, dossiers, resolution-quality verdicts,
  resolution receipts, and event-contract policy verdicts.
- Nonpublic/insider/hacked/classified/private/access-bypassed evidence is rejected at intake.
- Duplicate reporting collapses by independence group, stable dossier hashes are produced,
  and missing settlement sources block paper entry.
- `docs/forecast_receipt_contract.md` and `docs/data_retention_and_privacy.md` added.
- Phase D Forecast Desk neutral-engine bridge implemented.
- `assess_forecast` now turns normalized market + public dossier + independent probability
  + explicit costs into a paper-only `ForecastReceipt`.
- The usable edge enters sizing exactly once as raw commitment; neutral score/gate grade
  evidence quality and sample strength.
- Forecast receipt persistence added to the Forecast Desk ledger; schema version is now 2
  and frozen schema artifacts were refreshed.
- Regression tests cover 95% at 98c rejection, 62% at 43c paper candidate, market-price
  separation from independent probability, cost-eliminated edge rejection, and persisted
  paper-only receipts.
- Phase E cost-aware paper simulator and replay implemented.
- `paper.py` now produces executable-top paper fills, depth-aware partial fills, and
  settlement outcomes; midpoint is not used by default.
- `costs.py` and `kalshi/fees.py` add versioned cost/fee receipts, with explicit-zero Kalshi
  fee default until a reviewed schedule is supplied.
- `tools/forecast_desk_replay.py` and `docs/paper_simulation_methodology.md` added.
- Tests cover partial fills, settlement economics, paper labels, no-lookahead rejection, and
  versioned cost/fee validation.
- Phase F scoreboard, calibration, and self-funding gate implemented.
- `build_forecast_scoreboard` now reports resolved count, Brier score, market-baseline
  Brier score, category net paper result, and total net paper result.
- `self_funding.py`, `config/self_funding_standard.json`,
  `tools/forecast_desk_scoreboard.py`, and `tools/forecast_desk_self_funding.py` added.
- Verified self-funding claims are denied on paper mode, missing costs, zero costs, tiny
  samples, insufficient days, low ratio, or nonpositive net economic profit.
- `docs/forecast_calibration.md` and `docs/self_funding_standard.md` added.

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

Focused Phase C check before handoff update:

```text
python -m pytest tests\unit\test_event_dossiers.py tests\unit\test_resolution_rules.py tests\regression\test_event_contract_authority_boundaries.py -q
-> 11 passed
python -m pytest tests\unit\test_event_contracts.py -q
-> 17 passed
```

Phase C full-suite result:

```text
python -m pytest -q        -> 154 passed
python tools/check_invariants.py -> green
git diff --check           -> green
```

Focused Phase D check before handoff update:

```text
python -m pytest tests\regression\test_forecast_full_chain.py tests\regression\test_forecast_storage_lineage.py tests\regression\test_forecast_db_schema_frozen.py -q
-> 12 passed
python tools\freeze_forecast_db_schema.py --check -> green
python -m pytest tests\unit\test_forecast_calibration.py -q
-> 2 passed
```

Phase D full-suite result:

```text
python -m pytest -q        -> 161 passed
python tools/check_invariants.py -> green
git diff --check           -> green
```

Focused Phase E check before handoff update:

```text
python -m pytest tests\unit\test_paper_simulation.py tests\regression\test_forecast_replay_no_lookahead.py -q
-> 5 passed
python -m pytest tests\unit\test_forecast_costs.py -q
-> 2 passed
python tools\forecast_desk_replay.py --fixture --json -> paper manifest, no authority
```

Phase E full-suite result:

```text
python -m pytest -q        -> 168 passed
python tools/check_invariants.py -> green
git diff --check           -> green
```

Focused Phase F check before handoff update:

```text
python -m pytest tests\unit\test_self_funding.py tests\regression\test_self_funding_claim_gate.py tests\unit\test_forecast_scoring.py tests\unit\test_forecast_calibration.py -q
-> 8 passed
python tools\forecast_desk_scoreboard.py --fixture --json -> scoreboard emitted
python tools\forecast_desk_self_funding.py --fixture --json -> paper claim denied
```

Phase F full-suite result:

```text
python -m pytest -q        -> 174 passed
python tools/check_invariants.py -> green
git diff --check           -> green
```

## Next Phase

Continue to Phase G after Phase F is committed cleanly:

```powershell
python -m pytest -q
python tools\check_invariants.py
git diff --check
git add .
git commit -m "Add Forecast Desk scoreboard and self-funding proof ledger"
```

Then implement public FoxClaw Hunt export:

```text
foxclaw/adapters/event_contracts/publication.py
tools/forecast_desk_export_public.py
config/publication_policy.json
docs/public_hunt_policy.md
docs/press_experiment.md
tests/unit/test_public_forecast_export.py
```

## Watch

- Keep `engine/` free of Kalshi/event-contract vocabulary.
- Keep default tests offline and deterministic.
- Do not hardcode `C:\Users\brend\...` in code; use explicit args, environment variables,
  then repo-local fallback.
- Do not put Forecast Desk DBs under OneDrive.
- Treat Kalshi docs as live; changelog drift must become a later receipt watcher.
