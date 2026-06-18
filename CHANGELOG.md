# Changelog

All notable changes to FoxClaw are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning follows
[Semantic Versioning](https://semver.org/).

The version resets to `0.1.0` for this clean rebuild (`foxclaw-core`). The pre-v2 system is
preserved as the `v1-legacy` archive. Milestone map: `0.x` builds toward launch, one minor
bump per completed overhaul phase; **`1.0.0`** is earned at Apollo-2 cutover when v2 runs the
live track record and is demo-ready.

## [0.4.7] - 2026-06-18
### Added
- **Apollo Mesh V0.** Added local signed node events, HMAC-SHA256 canonical event sealing,
  local identity loading/creation, and append-only inbox/outbox logs.
- Added `tools/apollo_mesh.py` with `init`, `heartbeat`, `handoff`, `receive`, and `inbox`
  commands for A1/A2 structured node communication.
- Added `docs/apollo_mesh_v0.md` and linked it from the A1/A2 coordination docs.
- Tests cover event verification, tamper failure, forbidden command/secret fields,
  authority locks, idempotent local logs, and CLI round trips.
### Fixed
- Pinned paper-simulation settlement fixtures to deterministic forecast timestamps so the
  no-lookahead guard does not fail after the wall clock passes the fixture resolution time.
### Notes
- This is local-first and transport-neutral. Nostr/private relay transport can be added as
  an adapter after A1/A2 prove the event contract locally.

## [0.4.6] - 2026-06-18
### Added
- **Redshift Paper Boundary V1.** Added context-only FoxClaw decision exports,
  Redshift paper execution receipts, Redshift paper outcome receipts, and hash-link
  verification under `foxclaw.adapters.redshift.paper_boundary`.
- Added `tools/redshift_paper_boundary.py --fixture --json` to emit a deterministic
  FoxClaw decision -> Redshift paper execution -> Redshift outcome handshake.
- Tests prove Redshift cannot mutate FoxClaw decision fields, carry live order/account IDs,
  overfill paper size, introduce capital effect, or gain live authority.
### Notes
- This is the first working proof that paper trading can move toward Redshift through
  receipts without moving FoxClaw's decision authority.

## [0.4.5] - 2026-06-18
### Added
- Added `docs/progress_operating_model.md` to define progress across build, migration,
  decision-quality, paper-continuity, and node-coordination lanes.
- Added `docs/foxclaw_redshift_paper_boundary.md` to capture the recommended boundary:
  FoxClaw owns decisions and scoring; Redshift may rehearse paper execution through receipts.
### Notes
- Do not move all paper trading to Redshift in one step. Prove a paper receipt handshake
  first, then decide long-term ownership.

## [0.4.4] - 2026-06-18
### Added
- **Apollo Node Coordination V1.** Added `foxclaw.nodes.apollo` contracts and
  `tools/apollo_node_brief.py` for JSON or Markdown handoff receipts between A1, A2, and
  future Apollo nodes.
- Added `docs/apollo_node_coordination.md` with two-workstation rhythm, handoff commands,
  and failure modes.
- Updated the A1/A2 migration brief to point nodes at the Apollo node brief tool.
- Tests cover safe authority locks, dirty-file reporting, parseable CLI JSON, and Markdown
  handoff output.
### Notes
- Node communication remains read-only coordination. It does not inspect secrets, share a DB,
  grant runtime authority, or mutate the old A2 FoxClaw checkout.

## [0.4.3] - 2026-06-18
### Added
- Added `docs/a2_migration_context.md` as the A1/A2 coordination brief for the clean
  `foxclaw-core` migration.
- The brief gives A2 a paste-ready planning prompt, two-workstation VSCode/git rules,
  Keep / Cut / Port / Rebuild deliverable format, and next sprint guardrails.
### Notes
- A1 and A2 are two workstations on the same clean repo. The old A2 FoxClaw checkout remains
  legacy/reference runtime unless explicitly touched.

## [0.4.2] - 2026-06-18
### Added
- **Trusted Evidence Intake V1.** Added context-only trusted submitter, evidence packet,
  and validation contracts for Forecast Desk dossiers.
- `tools/forecast_evidence_intake.py` can write deterministic fixture or manual trusted
  evidence packets and validation receipts into the Forecast Desk ledger.
- Forecast DB schema version `3` adds `trusted_evidence_packets` and
  `trusted_evidence_validations`, with frozen schema artifacts refreshed.
- `docs/trusted_evidence_intake.md` documents the trust-to-submit, not trust-to-decide
  boundary, including the Redshift context-only lane and football evidence use case.
- Tests cover authority-field rejection, nonpublic validation rejection, duplicate evidence
  handling, CLI persistence, and all intake authority flags remaining false.
### Notes
- Trusted contributors can feed the matrix. They cannot set probabilities, publish,
  enter paper positions, submit orders, move funds, or authorize execution.

## [0.4.1] - 2026-06-18
### Added
- **Forecast Desk Phase H: continuous hunt loop scaffold and diagnostics.** Added
  `forecast_desk_doctor.py` and `forecast_desk_watch.py` with paper-only health receipts,
  explicit silence reasons, freshness receipt, and single-instance lock handling.
- Regression coverage verifies doctor silence reasons and watch-once status output.
### Notes
- Phase H is a safe once-mode scaffold. A bounded recurring scheduler can build on this
  without adding live authority.

## [0.4.0] - 2026-06-18
### Added
- **Forecast Desk Phase G: public FoxClaw Hunt export.** Added sanitized static export
  contracts, fixture CLI, publication policy, and public Hunt/press docs.
- `publication.py` builds paper-labeled public forecasts, excludes private/internal fields,
  preserves resolved losers, supports superseding IDs, and records an export hash.
- `tools/forecast_desk_export_public.py` writes `public_forecasts.json`,
  `public_forecasts.md`, `scoreboard.json`, `scoreboard.md`, and `build_log.json`.
- Tests cover paper labels, private-field exclusion, losing forecast preservation, export
  hash presence, and expected static files.
### Notes
- Public export is proof of process, not a profit or self-funding claim.

## [0.3.1] - 2026-06-18
### Added
- **Forecast Desk Phase F: scoreboard, calibration, and self-funding gate.** Added resolved
  forecast scoreboard aggregation with Brier score, market-baseline Brier score, category
  net paper result, and fixture CLI output.
- Added `self_funding.py`, `config/self_funding_standard.json`, and
  `tools/forecast_desk_self_funding.py` to deny verified self-funding claims unless sample,
  duration, cost receipts, ratio, profit, and mode standards are met.
- `docs/forecast_calibration.md` and `docs/self_funding_standard.md` document calibration and
  claim-gate doctrine.
- Tests cover market-baseline comparison, paper-mode claim denial, missing costs, zero-cost
  handling, and founder-live standard pass.
### Notes
- Paper results may be self-funding candidates only. They cannot become verified
  "FoxClaw pays for itself" claims.

## [0.3.0] - 2026-06-18
### Added
- **Forecast Desk Phase E: cost-aware paper simulator and replay.** Added executable
  top-of-book paper fills, depth-aware partial fills, versioned cost/fee receipts, settlement
  outcomes, and a replay no-lookahead guard.
- `paper.py` now produces paper-only `PaperPosition` and `PaperOutcome` receipts using
  YES/NO ask prices inferred from the bid-only book; midpoint is not used by default.
- `costs.py` and `kalshi/fees.py` add explicit cost and fee-model versions. The Kalshi fee
  default is explicit zero until a reviewed schedule is supplied.
- `tools/forecast_desk_replay.py` writes a deterministic paper replay manifest.
- `docs/paper_simulation_methodology.md` documents entry pricing, depth, fees, settlement,
  and no-lookahead rules.
- Tests cover partial fills, settlement economics, paper labels, no-lookahead rejection, and
  versioned cost/fee validation.
### Notes
- This minor bump marks the first complete read-only-to-paper chain: public market snapshot,
  public dossier, forecast receipt, executable paper fill, and settlement replay.

## [0.2.4] - 2026-06-18
### Added
- **Forecast Desk Phase D: neutral-engine bridge and forecast receipts.** Added
  `assess_forecast`, which takes a normalized market, public dossier, independent
  probability, and explicit costs, then produces a paper-only `ForecastReceipt`.
- Forecast receipt sizing keeps the edge single-owner rule: usable edge becomes the raw
  commitment exactly once, while neutral `engine.score` / `engine.gate` grade evidence
  quality and sample strength.
- `forecast_receipts` persistence was added to the Forecast Desk ledger, with schema version
  bumped to 2 and frozen schema artifacts refreshed.
- Regression tests cover the 95%-at-98c rejection, an attractive 62%-at-43c paper candidate,
  market-price separation from the independent probability, cost-eliminated edge rejection,
  and persisted paper-only receipts.
- Added small calibration helpers for Brier score and log loss.
### Notes
- Market price never mutates the independent probability. The adapter computes market
  implied probability and usable edge at the border, then hands neutral commitment/quality
  terms to the engine.

## [0.2.3] - 2026-06-18
### Added
- **Forecast Desk Phase C: public-evidence dossiers and resolution-quality gate.** Added
  frozen contracts for evidence eligibility, accepted evidence items, dossiers, resolution
  quality verdicts, resolution receipts, and event-contract policy verdicts.
- `dossiers.py` now rejects nonpublic/insider/hacked/classified/private/access-bypassed
  evidence before intake, collapses duplicate reporting by independence group, records
  rejected evidence verdicts, and produces stable dossier hashes.
- `resolution.py` now scores rule/source clarity and blocks paper entry when settlement
  sources or rule text are missing.
- `policy.py` keeps event-contract paper/public verdicts behind hard false authority fields.
- `docs/forecast_receipt_contract.md` and `docs/data_retention_and_privacy.md` document the
  receipt and privacy boundaries.
### Notes
- LLM or prose fields cannot override banned evidence classifications.
- Missing settlement source blocks paper entry; ambiguous markets can be watched but not
  treated as clean paper candidates.

## [0.2.2] - 2026-06-18
### Added
- **Forecast Desk Phase B: snapshot ledger and schema guard.** Added
  `foxclaw/adapters/event_contracts/storage/` with Forecast Desk DB resolution, cloud-sync
  path rejection, idempotent SQLite schema initialization, raw payload lineage, normalized
  snapshot repositories, sync cursors, and gzip JSONL raw response archiving.
- `tools/forecast_desk_sync.py` records read-only Kalshi fixture/live snapshots into a
  node-local ledger while preserving raw hashes for series, events, markets, and order books.
- `tools/freeze_forecast_db_schema.py`, `config/forecast_db_schema.frozen.json`, and
  `docs/forecast_db_schema.md` freeze the schema contract for review and drift checks.
- Regression tests cover schema idempotence, raw archive round-trip, normalized-row-to-raw
  lineage, no-duplicate fixture sync resume, frozen schema verification, and OneDrive path
  rejection.
### Changed
- `.gitignore` now ignores only a root `/storage/` runtime folder so source packages named
  `storage` are not accidentally hidden.
### Notes
- Forecast Desk storage defaults to explicit path, then `FOXCLAW_FORECAST_DB`, then
  `./data/forecast_desk.db`; it does not use OneDrive as a source of truth.

## [0.2.1] - 2026-06-18
### Added
- **Forecast Desk Phase A: read-only Kalshi API Desk.** Added a credential-free Kalshi REST
  adapter under `foxclaw/adapters/event_contracts/kalshi/`, including environment metadata,
  central GET transport with 429 backoff, cursor pagination guards, fixed-point `Decimal`
  parsing, normalization of series/events/markets, order-book reconstruction, and historical
  cutoff helpers.
- `tools/kalshi_api_desk.py` for read-only inspection (`doctor`, `series`, `events`,
  `markets`, `inspect`, `orderbook`, `trades`) with an offline fixture mode for deterministic
  default tests.
- Offline Kalshi fixtures plus unit/regression coverage for fixed-point parsing, YES/NO
  bid-to-ask inference, crossed-book invalidation, repeated pagination cursor rejection,
  historical routing, malformed float-money rejection, and credential-free CLI posture.
- `docs/kalshi_api_field_guide.md` documents the Phase A API boundary and read-only posture.
### Notes
- No credentials are loaded, no order endpoint is invoked, and all authority flags remain
  false / `A4_prohibited`.
- This is a patch bump because it adds the first production-shaped event-contract adapter
  while keeping the system read-only and paper-first.

## [0.2.0] — 2026-06-17
### Added
- **Engine phase complete — the market scoreboard *builder* adapter + the full decision
  chain** (v0.2.0 Pass 3). `foxclaw/adapters/market/scoreboard.py` is the customs border:
  market vocabulary (symbol/side/entry/exit/PnL/source_id) and the corruption filters stay
  here; only neutral terms cross into `engine/`.
  - **Full chain wired** (`assess_setup`): store paper outcomes → adapter builds neutral
    observations + per-subject aggregates → `engine.edge` estimates the edge → `engine.score`
    grades a tier → `engine.gate` applies the multiplier → one receipt-compatible verdict.
  - **Corruption filters = invariant #8 in code** (`clean_rows`): implausible single-trade
    returns (`RETURN_SANITY_CAP`), entry-price outliers vs the robust per-symbol median
    (`ENTRY_OUTLIER_RATIO`), excluded price/test sources, and `raw_events` duplicate dedup —
    so a mis-parsed price can't fake a track record.
  - **DB access delegated to the store** via new `PaperOutcomeStore.get_closed_outcomes_with_source`
    (outcomes joined to their journal's source), never a hardcoded path.
- **9 regression tests** (`tests/regression/test_market_scoreboard_adapter.py`): seeded
  fixture DB → both setups graded (winner boosts, catastrophe blocks), full-chain
  `assess_setup` (boost ×1.2 / block →0 / unknown →observe), neutral-observation shape, and
  each corruption/dedup filter. Full suite **100 green**.
### Notes
- Invariant guard green: the adapter holds all market vocabulary, so `engine/` stays
  domain-neutral (#4) and pure stdlib (#6). This completes the engine phase the v0.2.0 minor
  was reserved for (edge + trust + gate/score + P9 + the market chain). Next: ingest/parse +
  decide, then shadow-parity toward the A2 cutover (v1.0).

## [0.1.5] — 2026-06-17
### Added
- **Engine gate + scoring ported (v0.2.0 Pass 2 tail), decomposed on the way in** — the
  *neutral* decision logic into `foxclaw/engine/`, the market framing into `adapters/market/`:
  - `engine/score.py` ← scoreboard grader from `tools/setup_performance_summary.py`
    (`trust_tier`, `composite_score`, `decision_tier`), renamed to neutral terms
    (success_rate / reward_factor / mean_reward — no symbol/PnL identifiers).
  - `engine/gate.py` ← the edge authority from `tools/pre_decision_gate.py` (`evaluate` →
    `GateVerdict`), keyed by an **opaque subject**; safe `observe` fallback on
    missing/stale scoreboard or unknown subject; applies the min-N boost-suppression.
  - `adapters/market/setup.py` — the `source:symbol:side` key construction (market vocab
    stays in the adapter, invariant #4).
- **P9 RESOLVED — one owner of the decision-tier vocabulary:** new `engine/tiers.py` owns the
  tier set (`block/reduce/observe/allow/allow_boosted`), the `0/.5/.75/1/1.2` multiplier map,
  and the boost-suppression rule. `edge.decision_label`, `engine/score`, and `engine/gate` all
  defer to it instead of re-spelling the strings/multipliers — invariant #3 ("edge enters
  `final` exactly once") made literal at the code level. Two graders remain by design (edge =
  posterior probability, scoreboard = composite score); the gate *applies* the tier, never
  re-grades. See `docs/decisions.md` (2026-06-17 "P9 RESOLVED").
- **29 new unit tests** (`tests/unit/test_gate_score.py`): the canonical multiplier map,
  fallback-to-cautious on unknown tiers, boost-suppression shape; trust-tier thresholds,
  shrinkage to neutral on thin n, the decision-tier ladder; gate fallbacks, block-holds-at-0,
  boost suppression/threshold, and that the gate does not re-grade. Full suite green (91).
### Notes
- Invariant guard green over `engine/` after the port (#4 domain-neutral, #6 pure stdlib) —
  proof the new `tiers`/`score`/`gate` carry no market identifiers. **Still owed for v0.2.0**
  (per `docs/engine_port_plan.md`): the market scoreboard *builder* adapter (DB read +
  corruption filters = invariant #8, via `store/db.resolve_db` not a hardcoded path), and the
  Pass-3 regression test of the full `evidence → edge → gate` chain.

## [0.1.4] — 2026-06-17
### Added
- **Pure engine trio ported (v0.2.0 Pass 2)** into `foxclaw/engine/`, the first decision
  logic in the new repo — all pure stdlib, domain-neutral, no I/O:
  - `engine/edge.py` ← `bayesian_edge.py` (verbatim-clean): Beta-Binomial edge estimator
    with conservative Kelly, `BayesianEdge.verdict()`.
  - `engine/trust/reliability.py` ← `source_reliability.py`: `ρ_source` evidence weight
    (down-weight only; diagnostic per invariant #5).
  - `engine/trust/trustworthiness.py` ← `trustworthiness.py`: `ρ_trust` from claim
    well-formedness + `trust_haircut` (never un-blocks, only reduces).
- **Market-claim altitude split (resolves part of P1):** `market_claim_well_formed` moved
  out of the trust module to **`foxclaw/adapters/market/claims.py`**, so `engine/` stays
  domain-neutral while the market's well-formedness rule lives in the adapter. The neutral
  `Trustworthiness` consumes its `bool|None` via `ClaimQuality`.
- **33 engine/trust/adapter unit tests** in `tests/unit/` (Beta CDF/PPF, posterior,
  commitment + exploration floor, catastrophe veto, decision tiers, recency; ρ down-weight
  bounds, haircut safety shape, market claim sanity). Full suite green (62 tests).
### Notes
- The **invariant guard passes over `engine/` after the port** — proof the split kept the
  engine clean (#4) and pure-stdlib (#6). Still unported (per `docs/engine_port_plan.md`):
  gate + score (decompose; resolve pin P9 — one owner of the decision-tier vocabulary).
  v0.2.0 minor is reserved for engine-phase completion (incl. gate/score), not this patch.

## [0.1.3] — 2026-06-17
### Added
- **Paper-execution layer ported into `foxclaw/store/`**, completing the store receipt
  chain: `journal` (simulated action from a decision) → `outcomes` (positions, realized
  outcomes, position adjustments). Promoted from v1 `src/grovecore/{paper_journal,paper_outcomes}.py`.
- `paper_journal` carries `evaluate_paper_action_policy` (its single consumer): paper-trade
  actions require a `paper_candidate_intent` decision; live/funds/secret/destructive actions
  are blocked (invariant #1). `outcomes` adds `open_position`/`close_position`/`simulate_exits`
  and the portfolio summary (win rate, profit factor, drawdown, Sharpe).
- **`tests/regression/test_paper_execution_linkage.py`** — 13 contract tests (journal policy
  guards, full chain journal→position→outcome, long/short PnL signs, portfolio aggregation).
  Full suite green (27 tests).
- `normalize_key` added to `store/db.py` (shared by the paper modules).
### Notes
- Architecture-review flag (Phase 1): `outcomes.py` carries market vocabulary
  (`realized_pnl_usd`, `win_rate`, `sharpe`, long/short). It lives in `store/` per the
  documented port map, but whether the portfolio *metrics* belong in an analytics adapter is
  an open invariant-#4 question, recorded in the module rather than decided unilaterally.

## [0.1.2] — 2026-06-17
### Added
- **Decision-spine store ported into `foxclaw/store/`** (Phase 2, lowest-risk-first per the
  architecture migration order): `events` → `parse_attempts` → `candidates` → `decisions`,
  the auditable receipt chain that produced the track record. Promoted from v1
  `src/grovecore/*` with behavior preserved.
- **`foxclaw/store/db.py`** — shared, vendor-neutral storage base that fixes two v1 layout
  scars: the hardcoded DB path (now resolved via `--db` / `$FOXCLAW_DB` / repo-local) and
  helpers (`utc_now`, `slugify`, JSON, row mapping) duplicated across every store module.
- **`foxclaw/policy/decision_policy.py`** — the allow/escalate/block decision veto
  (ported from v1 `src/policy/fc_decision_policy.py`); enforces paper-only (invariant #1):
  every execution/funds/secret decision type is blocked at receipt creation.
- **`tests/regression/test_store_spine_linkage.py`** — 12 contract tests encoding the
  receipt-chain invariants (lineage required, policy veto, confidence bounds, duplicate
  idempotency). Full suite green (14 tests).
### Changed
- The live `grove_core.db` was **relocated off OneDrive** to a local, non-synced path
  (`C:\Users\brend\foxclaw\data\`) on the dev node, with `FOXCLAW_DB` set; enforces
  invariant #9 (no cloud-synced authoritative store). A2 mirrors this at cutover (Phase 3).

## [0.1.1] — 2026-06-17
### Added
- **Frozen DB schema as the carried-forward asset boundary** (invariant #8): one of the
  three Phase 1 exit criteria. `tools/freeze_db_schema.py` snapshots the live
  `grove_core.db` schema (21 tables, 54 indexes) into `config/db_schema.frozen.json`
  (canonical + SHA-256 fingerprint) and `docs/db_schema.md` (the diligence view).
- `tests/regression/test_db_schema_frozen.py` guards against silent schema drift — runs
  in CI without a DB (validates artifact self-consistency) and, when a live DB is reachable,
  asserts no drift.
### Notes
- DB is located vendor-neutrally via `--db` / `$FOXCLAW_DB` / `./data/grove_core.db` —
  never a cloud-sync path (invariant #5; no OneDrive/Google dependency).

## [0.1.0] — 2026-06-17
### Added
- Clean `foxclaw-core` scaffold: package layout (`engine` / `store` / `policy` / `adapters`
  / `contract`), `pyproject.toml` (pure-stdlib core, version sourced from `VERSION`),
  README, and the public-contract airlock stub.
- Repository created outside OneDrive by design (local-first; git is the source of truth).
