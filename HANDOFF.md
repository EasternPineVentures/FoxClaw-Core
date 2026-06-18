# HANDOFF - foxclaw-core

This file is the operational passoff for the clean FoxClaw company repo.
Read it before changing code, then verify with `git log --oneline -10` and the tests.

Last updated: 2026-06-18
Branch: `master`
Version: `0.4.5`
Working repo: `C:\Users\brend\dev\foxclaw-core`

## Current Lane

Forecast Desk / Kalshi-first event-contract intelligence is the active lane.

FoxClaw is a decision matrix first. Kalshi is one public-data adapter feeding the
receipt-driven decision machinery. The core `engine/` must remain domain-neutral; market
and venue language stays under `foxclaw/adapters/`.

Company posture:

- This repo is the clean migration target and public-ready work surface.
- Git is the handoff path.
- A1 and A2 are VSCode workstations on the same clean `foxclaw-core` git repo.
- A2 also has an old FoxClaw checkout that may still be useful runtime/reference material;
  treat that old checkout as legacy/read-only unless a task explicitly says otherwise.
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
- Phase G public FoxClaw Hunt export implemented.
- `publication.py`, `tools/forecast_desk_export_public.py`, `config/publication_policy.json`,
  `docs/public_hunt_policy.md`, and `docs/press_experiment.md` added.
- Public exports are paper-labeled, exclude private/internal fields, preserve losing/resolved
  forecasts, and include export hashes.
- Phase H continuous hunt loop scaffold and diagnostics implemented.
- `tools/forecast_desk_doctor.py` reports paper-only health and all standard silence reasons.
- `tools/forecast_desk_watch.py --once` writes status JSON with a freshness receipt and
  releases its lock file.
- Trusted Evidence Intake V1 implemented.
- `intake.py` adds trusted submitter, evidence packet, and intake validation contracts:
  trusted people can submit context, but cannot set probability, side, verdict, publication,
  paper entry, orders, funds movement, or execution authority.
- `tools/forecast_evidence_intake.py` writes fixture or manual trusted evidence packets plus
  validation receipts into the Forecast Desk ledger.
- Forecast DB schema version is now 3 with `trusted_evidence_packets` and
  `trusted_evidence_validations`; frozen schema artifacts were refreshed.
- `docs/trusted_evidence_intake.md` documents the trust-to-submit, not trust-to-decide
  boundary, including football evidence and Redshift context-only usage.
- A1/A2 migration coordination brief added in `docs/a2_migration_context.md`.
- The A2 planning default is `C first, then B`: produce a Keep / Cut / Port / Rebuild list
  from the old running A2 repo, then turn it into the next sprint plan.
- Apollo Node Coordination V1 added.
- `foxclaw.nodes.apollo` and `tools/apollo_node_brief.py` generate JSON or Markdown
  node handoff receipts with repo truth, current slice, next request, blockers, notes,
  dirty-file status, and all authority flags locked false.
- `docs/apollo_node_coordination.md` documents the A1/A2 handoff rhythm and failure modes.
- Progress Operating Model added in `docs/progress_operating_model.md`.
- FoxClaw/Redshift paper boundary note added in `docs/foxclaw_redshift_paper_boundary.md`.
- Current recommendation: do not move all paper trading to Redshift in one step. Keep
  FoxClaw as the decision matrix and prove a receipt handshake where Redshift can rehearse
  paper execution and return paper outcomes.

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

Focused Phase G check before handoff update:

```text
python -m pytest tests\unit\test_public_forecast_export.py -q
-> 4 passed
python tools\forecast_desk_export_public.py --fixture --write <temp> --json
-> public_forecasts.json/md, scoreboard.json/md, build_log.json
```

Phase G full-suite result:

```text
python -m pytest -q        -> 178 passed
python tools/check_invariants.py -> green
git diff --check           -> green
```

Focused Phase H check before handoff update:

```text
python -m pytest tests\regression\test_forecast_desk_watch_doctor.py -q
-> 2 passed
python tools\forecast_desk_doctor.py --fixture --json -> paper status emitted
python tools\forecast_desk_watch.py --once --fixture --status-file <temp> --lock-file <temp> --json -> status JSON and lock released
```

Phase H full-suite result:

```text
python -m pytest -q        -> 180 passed
python tools/check_invariants.py -> green
git diff --check           -> green
```

Focused Trusted Evidence Intake V1 check before handoff update:

```text
python -m pytest tests\unit\test_trusted_evidence_intake.py tests\regression\test_trusted_evidence_intake_cli.py tests\regression\test_forecast_db_schema_frozen.py tests\regression\test_forecast_storage_lineage.py -q
-> 14 passed
python tools\freeze_forecast_db_schema.py --check -> green
python tools\forecast_evidence_intake.py --fixture --db <temp> --json
-> accepted context-only evidence receipt, no authority
```

Trusted Evidence Intake V1 full-suite result:

```text
python -m pytest -q        -> 187 passed
python tools\check_invariants.py -> green
git diff --check           -> green; CRLF normalization warnings only on generated schema docs
```

A1/A2 migration brief verification:

```text
documentation-only phase; no runtime behavior changed
```

Focused Apollo Node Coordination V1 check before handoff update:

```text
python -m pytest tests\unit\test_apollo_node_brief.py tests\regression\test_apollo_node_brief_cli.py -q
-> 5 passed
python tools\apollo_node_brief.py --fixture --node-id A1 --peer-node A2 --current-slice "Apollo node coordination V1" --next-request "pull, read docs\apollo_node_coordination.md, then run the old-repo inventory" --note "old A2 repo is reference-only"
-> Markdown node brief emitted, authority false
```

Apollo Node Coordination V1 full-suite result:

```text
python -m pytest -q        -> 192 passed
python tools\check_invariants.py -> green
git diff --check           -> green
```

Progress/Redshift boundary documentation verification:

```text
documentation-only phase; no runtime behavior changed
python -m pytest -q        -> 192 passed
python tools\check_invariants.py -> green
git diff --check           -> green
```

## Next Phase

Next safe work:

- Add a private trusted-roster/auth boundary if this intake becomes multi-user instead of
  operator-run.
- Have A2 pull this repo, verify version/commit/tests, and run the read-only old-repo
  inventory described in `docs/a2_migration_context.md`.
- Use `python tools\apollo_node_brief.py --node-id A1 --peer-node A2` before handing
  active work from A1 to A2, and the reverse command before handing status back.
- Build a Redshift Paper Boundary V1 fixture before deciding whether paper runtime loops
  should move to Redshift.
- Add source-specific import adapters only after their trust and privacy boundaries are
  explicit.
- Continue to Phase I/J only after deciding whether to enter demo-auth work.

Phase I is demo-only authentication and WebSocket rehearsal. It should not start unless
demo credential boundaries are explicit. Phase J is documentation-only live execution gate.

```text
kalshi/auth.py
kalshi/websocket.py
docs/runbooks/kalshi_demo.md
docs/live_execution_gate.md
```

## Watch

- Keep `engine/` free of Kalshi/event-contract vocabulary.
- Keep default tests offline and deterministic.
- Do not hardcode `C:\Users\brend\...` in code; use explicit args, environment variables,
  then repo-local fallback.
- Do not put Forecast Desk DBs under OneDrive.
- Treat Kalshi docs as live; changelog drift must become a later receipt watcher.
