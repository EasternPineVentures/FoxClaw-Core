# HANDOFF - foxclaw-core

This file is the operational passoff for the clean FoxClaw company repo.
Read it before changing code, then verify with `git log --oneline -10` and the tests.

Last updated: 2026-06-19
Branch: `master`
Version: `0.4.15`
Working repo: `C:\Users\brend\dev\foxclaw-core`

## Current Lane

FoxClaw Gym / June 28 demo readiness is the active lane.
Trading Intelligence Fabric Phase 0 / public contract foundations remains the current
architecture lane.
Forecast Desk / Kalshi-first event-contract intelligence remains the current implemented
intelligence lane.

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
- Redshift Paper Boundary V1 implemented.
- `foxclaw.adapters.redshift.paper_boundary` now provides a context-only
  `FoxClawDecisionExport`, `RedshiftPaperExecutionReceipt`, `RedshiftPaperOutcomeReceipt`,
  and hash-link verification.
- `tools/redshift_paper_boundary.py --fixture --json` emits a deterministic FoxClaw
  ForecastReceipt -> Redshift paper execution -> Redshift paper outcome receipt chain.
- Tests prove Redshift cannot mutate FoxClaw decision fields, carry live order/account IDs,
  overfill paper size, introduce capital effect, or gain live authority.
- Apollo Mesh V0 implemented.
- `foxclaw.nodes.mesh` provides local signed node events using canonical JSON plus
  HMAC-SHA256, with hard false authority locks and content filtering for commands/secrets.
- `foxclaw.nodes.mesh_store` provides append-only local inbox/outbox JSONL logs under
  gitignored `data/`.
- `tools/apollo_mesh.py` adds `init`, `heartbeat`, `handoff`, `receive`, and `inbox`
  commands for A1/A2 structured node communication.
- `docs/apollo_mesh_v0.md` documents the local-first mesh contract and the later relay path.
- Founder Node Security hardening added.
- Apollo Mesh V0 is now explicitly founder-only: events carry `node_role=founder_node`,
  `data_classification=founder_private`, `redistribution=do_not_export`, and
  `public_export_allowed=false`.
- `docs/founder_node_security.md` documents Apollo nodes as founder/IP-protected nodes;
  public/community nodes require a separate sanitized contract later.
- Apollo Mesh founder secret enrollment added.
- `tools/apollo_mesh.py doctor` reports local mesh identity, inbox/outbox counts, and public
  key ID without printing secrets or creating identity state.
- `tools/apollo_mesh.py rekey --secret-file <local-secret-file>` enrolls A1/A2 into the same
  private founder mesh secret without printing the secret.
- A2's local heartbeat proves it is online; A1/A2 cross-node verification requires matching
  `key_id` after shared-secret enrollment.
- Apollo Mesh `receive` now tolerates UTF-8 BOM and UTF-16 BOM JSON event files, so Windows
  editor/PowerShell formatting does not block signed event verification.
- `docs/apollo_mesh_v0.md` documents the accepted event-file encodings for local file
  handoff.
- Apollo Mesh private file-drop exchange added.
- `tools/apollo_mesh.py sync` exports local outbox events and imports verified peer events
  from a private exchange folder.
- `tools/apollo_mesh.py pulse` emits a founder heartbeat and runs `sync` in one command.
- `foxclaw.nodes.mesh_exchange` writes one event per JSON file, skips own/duplicate events,
  and reports rejected files without printing secrets.
- Forecast Learning Spine V1 added.
- `foxclaw.adapters.event_contracts.learning` creates paper-only `ForecastLearningReceipt`
  artifacts from ForecastReceipt + PaperOutcome pairs.
- `tools/forecast_learning_spine.py --fixture --json` emits a deterministic learning receipt
  with market baseline Brier comparison, paper result, and learning signal.
- Forecast DB schema version is now 4 with `forecast_learning_receipts`.
- `docs/forecast_learning_spine.md` documents the learning loop and authority boundary.
- Trading Intelligence Fabric Phase 0 added as contract/doctrine-only scaffolding.
- `docs/PROJECT_INDEX.md` is now the start-here orientation layer for future agents and
  ChatGPT handoffs.
- `docs/project_boundaries.md`, `docs/trading_intelligence_fabric.md`, and ADRs under
  `docs/adr/` define the GitHub coordination rule, the five information planes, the
  attention-is-not-evidence boundary, and the signal-is-not-trade boundary.
- `docs/integrations/coinfox.md`, `docs/integrations/planifier.md`, and
  `docs/integrations/foxclaw_node.md` record owner repo, status, resume location, and
  boundary rules for each future system.
- `foxclaw/contract/public/` now contains public schema scaffolds for public intelligence
  cards, public scorecards, attention receipts, and risk classifications.
- Public contract fixtures and `tests/unit/test_public_contract_schemas.py` validate the
  required schema shape and authority locks.
- FoxClaw Gym added as the first-encounter readiness and next-attention surface.
- `config/foxclaw_gym_drills.json` tracks demo-critical drills, proof commands, due dates,
  current status, demo lines, and next actions for the June 28 family-demo target.
- `foxclaw.gym` and `tools/foxclaw_gym.py` produce Markdown or JSON readiness reports with
  authority locks and the next attention list.
- `docs/first_encounter_guide.md` and `tools/foxclaw_visitor_guide.py` provide the
  plain-language opening surface for non-traders and curious family/wedding guests.
- `docs/foxclaw_gym.md`, `docs/demo_readiness_2026_06_28.md`, and
  `docs/demo_script_2026_06_28.md` define the readiness loop and optional showing notes.
- The family-demo order is FoxClaw -> CoinFox -> Planifier. Planifier already exists as a
  built product, but needs focused integration/polish work before it becomes the practice
  layer for this flow.
- CoinFox is documented as having social trading bones already, but needing major work to
  become the familiar open feed we want: posts, comments, branching replies, upvotes,
  live discussion, long-running trade ideas, and spotlight surfaces. FoxClaw may provide
  context there, but CoinFox owns the social feel and implementation.
- `docs/security_public_demo_threat_model.md` records public-demo attack surfaces and
  pre-demo security checks.
- `tools/public_intelligence_card_demo.py` renders the public intelligence fixture as
  demo-friendly Markdown, with public text escaped before rendering.
- Gym manifest validation rejects unsafe proof commands that reference live, secret, wallet,
  funds, order, or rekey paths.
- Internal intelligence contract v1 foundation added under `foxclaw/contract/internal/`.
  It defines the private RawSourceEvent -> ParseAttempt -> ClaimPacket -> EvidenceBundle ->
  AttentionAggregate -> TradeabilitySnapshot -> TradeReadinessVerdict ->
  PublicationDecision -> VerifiedOutcome path with sanitized fixtures and lineage tests.
  Parser behavior still waits for A2's legacy Discord inventory.
- Publication safety gate added under `foxclaw/policy/`: default `INTERNAL_ONLY`,
  private-source scanning, prompt/markup/performance-claim rejection, attention-boundary
  checks, and security tests proving private Discord content cannot cross the public gate.
- Professional readiness layer added under `foxclaw/engine/`, `foxclaw/adapters/market/`,
  and `foxclaw/policy/readiness.py`. It keeps attention, evidence quality, signal
  confidence, cost-adjusted edge, tradeability, entry quality, risk, plan readiness, source
  track record, and setup track record separate. `GOOD_SIGNAL_BAD_TRADE` is now a first-class
  verdict.
- Public Contract v1 frozen under `foxclaw/contract/public/` with `manifest.json`,
  `VERSION`, contract changelog, v1 schemas, public fixtures, scenario cards, verified
  outcomes, and deterministic CoinFox exporters:
  `tools/export_public_intelligence.py`, `tools/export_public_scorecard.py`, and
  `tools/render_public_intelligence_card.py`.

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

Focused Redshift Paper Boundary V1 check before handoff update:

```text
python -m pytest tests\unit\test_redshift_paper_boundary.py tests\regression\test_redshift_paper_boundary_cli.py -q
-> 7 passed
python tools\redshift_paper_boundary.py --fixture --json
-> linked FoxClaw decision export, Redshift paper execution, and Redshift paper outcome;
   authority false, redshift_capital_effect none
```

Redshift Paper Boundary V1 full-suite result:

```text
python -m pytest -q        -> 199 passed
python tools\check_invariants.py -> green
git diff --check           -> green
```

Focused Apollo Mesh V0 check before handoff update:

```text
python -m pytest tests\unit\test_apollo_mesh_events.py tests\regression\test_apollo_mesh_cli.py -q
-> 8 passed
python tools\apollo_mesh.py --mesh-dir <temp> --node-id A1 --fixture --json handoff --to-node A2 --summary "Apollo Mesh V0 local signed events are ready" --current-slice "apollo mesh v0" --next-request "pull, run apollo mesh tests, and send A2 heartbeat"
-> signed handoff.note event emitted, authority false
```

Apollo Mesh V0 full-suite result:

```text
python -m pytest -q        -> 207 passed
python tools\check_invariants.py -> green
git diff --check           -> green
```

Focused Founder Node Security check before handoff update:

```text
python -m pytest tests\unit\test_apollo_mesh_events.py tests\regression\test_apollo_mesh_cli.py -q
-> 9 passed
python tools\apollo_mesh.py --mesh-dir <temp> --node-id A1 --fixture --json heartbeat --message "founder node online"
-> signed founder_private heartbeat emitted, public_export_allowed false
```

Founder Node Security full-suite result:

```text
python -m pytest -q        -> 208 passed
python tools\check_invariants.py -> green
git diff --check           -> green
```

Focused Apollo Mesh founder enrollment check before handoff update:

```text
python -m pytest tests\unit\test_apollo_mesh_events.py tests\regression\test_apollo_mesh_cli.py -q
-> 12 passed
```

Apollo Mesh founder enrollment full-suite result:

```text
python -m pytest -q        -> 211 passed
python tools\check_invariants.py -> green
git diff --check           -> green
```

Apollo Mesh Windows event-file tolerance full-suite result:

```text
python -m pytest -q        -> 212 passed
python tools\check_invariants.py -> green
git diff --check           -> green
```

Apollo Mesh private file-drop exchange full-suite result:

```text
python -m pytest tests\regression\test_apollo_mesh_cli.py tests\unit\test_apollo_mesh_events.py -q
-> 15 passed
python -m pytest -q        -> 214 passed
python tools\check_invariants.py -> green
git diff --check           -> green
```

Forecast Learning Spine V1 focused check before handoff update:

```text
python -m pytest tests\unit\test_forecast_learning.py tests\regression\test_forecast_learning_spine_cli.py tests\regression\test_forecast_storage_lineage.py tests\regression\test_forecast_db_schema_frozen.py -q
-> 11 passed
python tools\freeze_forecast_db_schema.py --check -> green
python tools\forecast_learning_spine.py --fixture --json
-> learning_signal reinforce, decision_quality foxclaw_outperformed_market, authority false
```

Forecast Learning Spine V1 full-suite result:

```text
python -m pytest -q        -> 218 passed
python tools\check_invariants.py -> green
git diff --check           -> green; CRLF normalization warnings only on generated schema docs
```

A1/A2 founder mesh enrollment receipt:

```text
A1 key_id -> mesh-key:fb65caccc2c953e8
A2 heartbeat signer_key_id -> mesh-key:fb65caccc2c953e8
python tools\apollo_mesh.py --node-id A1 --json receive --event-file <A2 heartbeat>
-> received true
python tools\apollo_mesh.py --node-id A1 --json inbox
-> count 1, A2 founder heartbeat present
```

Trading Intelligence Fabric Phase 0 full-suite result:

```text
python -m pytest tests\unit\test_public_contract_schemas.py -q -> 4 passed
python tools\check_invariants.py -> green
python -m pytest -q -> 222 passed
git diff --check -> no whitespace errors; CRLF normalization warning only on docs\decisions.md
```

FoxClaw first-encounter / gym focused result:

```text
python tools\foxclaw_visitor_guide.py --fixture -> first-encounter guide emitted
python tools\foxclaw_gym.py --fixture -> training, 6/10 demo-critical ready, 0 blocked
python tools\public_intelligence_card_demo.py --fixture -> readable public card emitted
python -m pytest tests\unit\test_foxclaw_gym.py tests\unit\test_foxclaw_visitor_guide.py tests\unit\test_public_intelligence_card_demo.py tests\unit\test_public_contract_schemas.py -q -> 19 passed
python -m pytest -q -> 237 passed
python tools\check_invariants.py -> green
```

## Next Phase

Next safe work:

- Use `python tools\foxclaw_visitor_guide.py` as the first thing to show a non-trader.
- Run `python tools\foxclaw_gym.py` at the start of each work session and take the top
  `next_attention` item as the next smallest safe slice.
- Keep `docs/first_encounter_guide.md` understandable without a live explanation before
  adding more features.
- Review `docs/security_public_demo_threat_model.md` before the first full dry run.
- Create or map the GitHub project fields/issues for P17 so each repo owns its work.
- Keep Phase 1 contract-first: CoinFox attention receipts are sanitized aggregates, not
  CoinFox internals inside this repo.
- Current FoxClaw foundation stop line: do not keep expanding FoxClaw indefinitely before
  CoinFox. After A2's Discord parser inventory is reviewed, either finish the parser parity
  slice or explicitly mark it deferred, then move to the CoinFox repo.
- Have A2 pull `0.4.15`, run the focused learning and public-contract tests, and send a `pulse` through the
  private Apollo exchange folder.
- Add a private trusted-roster/auth boundary if this intake becomes multi-user instead of
  operator-run.
- Expand Learning Spine V1 from deterministic fixture receipts into real ledger replay over
  resolved Forecast Desk paper positions.
- Have A2 pull this repo, verify version/commit/tests, and run the read-only old-repo
  inventory described in `docs/a2_migration_context.md`.
- Use `python tools\apollo_node_brief.py --node-id A1 --peer-node A2` before handing
  active work from A1 to A2, and the reverse command before handing status back.
- Use `python tools\apollo_mesh.py --node-id A2 --json pulse --message "A2 active"` after
  A2 pulls this version, then run `sync` on A1 against the same private exchange folder.
- Keep Apollo Mesh V0 founder-only. Do not connect public/community nodes until a separate
  sanitized contract exists.
- Have A2 compare the Redshift Paper Boundary V1 fields against the old paper runtime
  inventory, then decide what maps, what gets cut, and what remains Redshift-only.
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
