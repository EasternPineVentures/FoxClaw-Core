# FoxClaw Deferred Decisions & Open Questions ("the pins")

We are laying out the city — package boundaries, how data flows, where each concern
lives — not finishing every building. Along the way we keep hitting things that *need*
more work but should **not** stop the layout: vocabulary that brushes a boundary,
two modules drifting toward the same job, a table whose home isn't settled yet.

This file is where those get **pinned**: named, given enough context to resume cheaply,
and tagged with the moment they should be picked up — so nothing rots into a silent
`# TODO` and no one re-derives it later. A pin is not a bug and not a decision; it's a
**deliberate, dated deferral**. When a pin is resolved, record the choice in
`docs/decisions.md` and strike the pin here (supersede, don't delete the history).

**Status tags:** 🔭 needs-design-review · 🧹 cleanup/DRY · 🚧 blocked-on-later-phase ·
❓ open-question. **Each pin:** what · why deferred · trigger (when to pick it up).

---

## P1 · 🔭 Where the domain-neutral / market line is drawn in `store/`
**What:** `foxclaw/store/outcomes.py` carries market vocabulary — `realized_pnl_usd`,
`win_rate`, `profit_factor`, `sharpe`, `long`/`short`, `symbol`. Invariant #4 says the
*core* speaks decision/outcome/reward, never PnL/win/loss. The store is the data layer,
not the brain, so the receipt *tables* arguably belong here — but `get_portfolio_summary`
(win rate, drawdown, Sharpe) is **analytics**, which may belong in an adapter.
**Why deferred:** drawing this line correctly depends on what `engine/` and
`adapters/market/` actually look like; deciding it before they exist would be guessing.
**Trigger:** the Phase 1 architecture review, or when `engine/` is built — whichever first.
Resolve as: keep storage in `store/`, move metric *computation* to `adapters/market` or an
`analytics/` surface, or accept the altitude with an explicit note in `architecture.md`.

## P2 · ❓ `live_trade_receipts` table vs paper-only (invariant #1)
**What:** the frozen schema carries a `live_trade_receipts` table (23 cols, 5 rows). It's
a live-execution concept in a paper-only system. It was almost certainly a *record-only*
table for the allowed `manual_live_exposure_tracking` domain — but that's unconfirmed.
**Why deferred:** it isn't on the store port path yet, and the asset boundary (frozen
schema) preserves it regardless; no need to decide its v2 home to keep moving.
**Trigger:** when classifying the remaining grovecore modules (P3). Decide: port as a
read-only exposure record, or leave it in the carried schema unused. Must not become a
live-execution write path.

## P3 · 🚧 Remaining GroveCore modules not yet ported or classified
**What:** the store port covered the receipt spine + paper execution. Still unported and
not yet assigned a v2 home (`engine/`, `store/`, `adapters/`, or cut): `bayesian_edge`,
`source_reliability`, `trustworthiness`, `source_trust`, `strategy_learning`,
`learning_memory`, `paper_learning_epoch`, `attention_budget`, `advisory_receipts`,
`control_receipts`, `market_move_monitor`, `live_trade_receipts` (see P2).
**Why deferred:** these are the *next* phases (engine, trust, policy). Porting them now,
before their package boundaries are set, is how modules end up stepping on each other.
**Trigger:** per-phase — `bayesian_edge` → `engine/edge` (v0.2.0); the source/trust trio →
`engine/trust` (diagnostic-only, invariant #5); `strategy_learning` → decompose, keep only
the concentration role (invariant #3). The high-level keep/cut/port call already lives in
`docs/foxclaw_v2_inventory.md`; this pin tracks the per-module execution.
**Update 2026-06-17:** all 12 modules now classified per-module (KEEP_ENGINE / STORE /
ADAPTER / REVIEW) with port recipes in **`docs/engine_port_plan.md`** (v0.2.0 Pass 1
survey). Pass 2 = port the pure trio (`edge`, `reliability`, `trustworthiness`); `gate` +
`scoring` need a supplementary `tools/` survey first (they aren't in this P3 set).

## P4 · 🧹 One canonicalizer, three copies
**What:** lowercase/underscore key normalization exists as `store/db.normalize_key`,
`policy/decision_policy._clean`, and an inlined `.strip().lower().replace(...)` in
`store/decisions.py`. Same function, three homes.
**Why deferred:** purely cosmetic; collapsing it now would churn already-committed,
tested files for no behavior change.
**Trigger:** next time any of those files is touched for real work — fold them onto
`store/db.normalize_key` (or a shared `foxclaw/_text.py` if policy shouldn't import store).

## P5 · 🧹 `resolve_db` duplicated in the freeze tool
**What:** `tools/freeze_db_schema.py` has its own `resolve_db` with the same semantics as
`foxclaw/store/db.resolve_db`. The tool can't simply `import foxclaw` when run as a
script (its dir, not the repo root, is on `sys.path`).
**Why deferred:** the duplication is ~10 lines with identical behavior; not worth a
fragile `sys.path` bootstrap mid-migration.
**Trigger:** when we establish a shared `tools/` bootstrap (repo-root on path) or package
the project — then the tool imports the canonical resolver.

## P6 · 🚧 Tool-dependent regression tests not ported
**What:** v1's linkage contract tests also exercised `reality_audit`, `record_decision`,
`record_paper_action`, and `proof_chain_smoke`. The v2 store tests cover the store
contracts only; those tool checks were dropped.
**Why deferred:** the tools themselves aren't ported yet.
**Trigger:** when the `tools/` keepers are ported — bring their tests with them.

## P7 · 🚧 A2 production DB relocation off OneDrive
**What:** the dev node (A1) DB was relocated to a local path and `FOXCLAW_DB` set. A2
(the live organism) still runs on its OneDrive-pathed DB and must be moved at cutover.
**Why deferred:** invariant #2 — A2 never stops; the move happens at Phase 3 cutover, not
mid-build. (Already recorded in the Phase 3 section of `docs/foxclaw_v2_overhaul_plan.md`;
mirrored here so the master pin list is complete.)
**Trigger:** Phase 3 cutover — copy to a local path, set `FOXCLAW_DB`, keep OneDrive copy
as read-only fallback until parity is signed off, then retire it.

## P8 · ❓ Rename "the analyst" in the FC vocabulary
**What:** the ecosystem term **"analyst"** is to be renamed. Today the codebase mostly says
**"source"** (e.g. `source_id`, `SourceReliability`, whose docstring glosses a source as
"an analyst, feed, agent, node"); "analyst" appears as an *example* of a source, not a
first-class identifier. The rename target is **not yet chosen**.
**Why deferred:** needs the founder's chosen name before any edit; renaming an identifier
that threads through schema (`source_id`), stores, and the frozen DB schema is a
cross-cutting change that must be done deliberately, not ad hoc.
**Trigger:** once the new name is chosen — decide scope first: is this a *display/vocabulary*
rename (docs, UI, CoinFox surface) only, or does it touch identifiers/columns? The frozen
schema (`source_id`) is an asset boundary (invariant #8), so a column-level rename is a
schema-migration decision, not a find-replace. Default recommendation: rename at the
**vocabulary/display layer**, keep `source_*` as the stable internal identifier.

## ~~P9 · 🔭 One owner for the decision-tier vocabulary~~ — ✅ RESOLVED 2026-06-17
**Resolution:** created `foxclaw/engine/tiers.py` as the single owner of the tier set, its
multiplier map, and the boost-suppression rule. `edge.decision_label`, `engine/score`, and
`engine/gate` all import from it; the gate *applies* a tier and never re-grades. Recorded in
`docs/decisions.md` (2026-06-17 "P9 RESOLVED"). The gate + scoring port that forced this was
decomposed on the way in (neutral logic → `engine/`, market `source:symbol:side` key →
`adapters/market/setup.py`). *Original pin below, kept for history.*

> **What:** the tier set `block / reduce / observe / allow / allow_boosted` (and its 0 / .5 /
> .75 / 1 / 1.2 multipliers) was defined **independently in three places** in v1:
> `bayesian_edge.decision_label()`, the scoreboard builder, and the gate.
> **Why deferred:** it only needed resolving when the engine port reached gate + scoring.
> **Trigger:** when porting `engine/gate.py` + `engine/score.py`.

---

## Process note — layering, so things don't step on each other
Package `__init__` exports must match the layer/phase they belong to. (Caught during the
3-commit store landing: a full `store/__init__` that imported `journal`/`outcomes` would
have broken the decision-spine commit, which didn't yet contain those modules.) Rule of
thumb: **an `__init__` may only export what its own commit/phase introduces.** When
splitting work across commits or phases, stage the `__init__` to match.

---

See `docs/decisions.md` for decisions already made, `docs/invariants.md` for the hard
rules, and `docs/foxclaw_v2_overhaul_plan.md` for the phase plan these pins slot into.
