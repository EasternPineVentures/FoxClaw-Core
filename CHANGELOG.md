# Changelog

All notable changes to FoxClaw are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/); versioning follows
[Semantic Versioning](https://semver.org/).

The version resets to `0.1.0` for this clean rebuild (`foxclaw-core`). The pre-v2 system is
preserved as the `v1-legacy` archive. Milestone map: `0.x` builds toward launch, one minor
bump per completed overhaul phase; **`1.0.0`** is earned at Apollo-2 cutover when v2 runs the
live track record and is demo-ready.

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
