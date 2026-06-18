# FoxClaw v2 — Engine Port Plan (v0.2.0, Pass 1: SURVEY ONLY)

**Generated:** 2026-06-17 · **Status:** survey, no code ported · resolves pin **P3** in
`docs/deferred.md`. Companion to `docs/architecture.md` (the target layout) and
`docs/foxclaw_v2_inventory.md` (the high-level keep/cut call).

> **Scope discipline (held):** this pass changed no runtime behavior, ported no code,
> did not touch A2, did not move the A2 DB, and did not branch into UI / CoinFox /
> Discord / public-node work. It only reads the remaining GroveCore modules and assigns
> each a v2 home + a port recipe.

**Classification legend:** `KEEP_ENGINE` (pure decision logic → `foxclaw/engine/`) ·
`STORE` (per-node persistence → `foxclaw/store/`) · `ADAPTER` (market/vendor-specific →
`foxclaw/adapters/`) · `CUT_ARCHIVE` (do not port; keep in v1-legacy) · `REVIEW`
(decompose or decide before porting).

## Classification at a glance

| Module | LOC | Class | Pure? | Writes DB? | v4 market vocab? | v2 home |
|---|---|---|---|---|---|---|
| `bayesian_edge.py` | 392 | **KEEP_ENGINE** | yes | no | clean | `engine/edge.py` |
| `source_reliability.py` | 191 | **KEEP_ENGINE** | yes | no | clean | `engine/trust/reliability.py` |
| `trustworthiness.py` | 195 | **KEEP_ENGINE** (split) | yes | no | one fn leaks | `engine/trust/trustworthiness.py` + adapter |
| `source_trust.py` | 671 | **STORE** | no | yes | mild | `store/source_trust.py` |
| `learning_memory.py` | 391 | **STORE** | no | yes | yes | `store/learning.py` |
| `attention_budget.py` | 568 | **STORE** | no | yes | no | `store/attention.py` |
| `advisory_receipts.py` | 368 | **STORE** | no | yes | no | `store/advisory.py` |
| `control_receipts.py` | 477 | **REVIEW→STORE** | no | yes | yes | `store/control.py` (paper-bound) |
| `market_move_monitor.py` | 283 | **ADAPTER** | yes | no | yes (by design) | `adapters/market/move_monitor.py` |
| `strategy_learning.py` | 1894 | **REVIEW** (decompose) | no | yes | yes | split: engine + store + policy |
| `paper_learning_epoch.py` | 618 | **REVIEW** | no | reads only | yes | analytics tool or `adapters` |
| `live_trade_receipts.py` | 435 | **REVIEW** (pin P2) | no | yes | yes (live) | decide: read-only record or don't port |

---

## KEEP_ENGINE — the pure decision core (port these first)

These three are the crown jewels: pure standard library, no I/O, explicitly
domain-neutral. They are the safest, highest-value port and define the `engine/`.

### 1. `bayesian_edge.py` → `foxclaw/engine/edge.py`
- **Decision function it owns:** "given an arm's outcome history, what is `P(EV>0)` and
  how hard to commit?" — `BayesianEdge.verdict()` → `EdgeVerdict` (prob_edge,
  expected_value, kelly, commitment, decision_label). Also the pure-Python Beta CDF/PPF
  (`beta_cdf`, `beta_ppf`) reused by the trust modules.
- **Reads:** in-memory `Observation(success, magnitude, age_days)` only. Nothing else.
- **Must NOT write / must NOT do:** no DB, no files, no network, no orders, no funds — it
  is pure computation. The market→Observation mapping stays in the *caller* (adapter).
- **Invariant #4 (domain-neutral):** ✅ clean — speaks arm/success/magnitude/reward/cost,
  never trade/PnL. **#6 (pure stdlib):** ✅ hand-rolled Beta, no numpy/scipy.
- **Minimum tests before porting:** port v1 `test_bayesian_edge.py`; assert (a) `beta_cdf`
  against known values + monotonicity + bounds, `beta_ppf` inverts it; (b) posterior
  updates with successes/failures; (c) `probability_of_edge` threshold `c/(r+c)`;
  (d) `commitment` for prob/kelly/min; (e) catastrophe veto returns 0; (f) thin-arm
  exploration floor; (g) `decision_label` tier mapping; (h) recency half-life weighting.

### 2. `source_reliability.py` → `foxclaw/engine/trust/reliability.py`
- **Decision function it owns:** per-source (and source×category) **evidence weight**
  `ρ_source ∈ [floor, 1]` from whether claims later resolved usefully —
  `SourceReliability.reliability()`.
- **Reads:** in-memory add() calls (source_id, useful flag, age, category). No I/O.
- **Must NOT write / must NOT do:** no DB; **never returns > 1.0** (down-weight only) and
  **never caps final size** — it weights the edge posterior, nothing more.
- **Invariant #4:** ✅ clean. **#5 (ρ is diagnostic, weights-not-caps, not yet folded into
  the live edge):** this module is *built* to honor #5, but per `docs/decisions.md`
  (2026-06-15) it stays a **shadow diagnostic** in v2 too — port it, do not wire it into
  live sizing without the shadow-first ritual (invariant #2).
- **Minimum tests:** port v1 `test_source_reliability.py`; assert ρ stays in `[floor,1]`
  and never exceeds 1; unknown source → `rho_unknown`; hierarchical category→global
  shrinkage; thin/down_weighted/trusted status thresholds.

### 3. `trustworthiness.py` → `foxclaw/engine/trust/trustworthiness.py` **(split)**
- **Decision function it owns:** per-source **trust** `ρ_trust ∈ [floor,1]` from *claim
  well-formedness* (not outcomes) — `Trustworthiness.trust()` — and the safe application
  `trust_haircut()` (can only reduce an already-cleared size; **never un-blocks**).
- **Reads:** in-memory `ClaimQuality(well_formed, age_days)`. No I/O.
- **Must NOT write / must NOT do:** no DB; `trust_haircut` must never raise size or weaken
  a block (the Pass-3 failure it was designed to prevent).
- **Invariant #4:** ⚠️ **one leak** — `market_claim_well_formed(side, entry, stop, target)`
  is market-specific (long/short, price levels). **Split on port:** the generic
  `Trustworthiness` + `trust_haircut` go to `engine/`; `market_claim_well_formed` moves to
  `adapters/market/` as the market's definition of "well-formed claim." This is exactly
  the P1 altitude line, made concrete.
- **Minimum tests:** ρ_trust down-weight-only; `trust_haircut` leaves blocks at 0 and only
  scales cleared sizes down; unassessable claim (`well_formed=None`) ignored, not penalized;
  (in the adapter) `market_claim_well_formed` level/side sanity + RR bounds.

---

## STORE — persistence layers (port during a later store pass, not engine)

These carry SCHEMA + DB writes — they are the data layer, not decision logic. They follow
the same `store/db.py` base the spine port established.

- **`source_trust.py` → `store/source_trust.py`.** Persists `source_trust_state` +
  `source_trust_adjustments` (`authority_level='advisory_only'`). ⚠️ contains
  classification heuristics (`POSITIVE/NEGATIVE_CLASSIFICATIONS`, `EXECUTION_TERMS`) — on
  port, the *scoring* should defer to `engine/trust`, leaving this module as persistence
  only. Mild market vocab.
- **`learning_memory.py` → `store/learning.py`.** Persists `learning_receipts` (lesson +
  mistake tags) and nudges source trust. ⚠️ market vocab (`symbol`, `side`,
  `realized_pnl_usd`) → P1. The lesson/mistake-tag *generation* is `REVIEW` (may move to
  engine/analytics); the receipt persistence is STORE.
- **`attention_budget.py` → `store/attention.py`.** Persists `attention_packets`
  (token-budget governance for LLM intake). The *budget policy* arguably belongs in
  `policy/`; the packet record is STORE.
- **`advisory_receipts.py` → `store/advisory.py`.** Persists LLM advisory output
  (model/provider/tokens/cost, `authority_level='advisory_only'`). The LLM *call* belongs
  in `adapters/llm`; this is just the receipt.
- **`control_receipts.py` → `REVIEW→store/control.py`.** Persists control actions
  (`pair`, `side`, `requested_notional/leverage`, `mode`). ⚠️ market + execution vocab →
  confirm it is paper/record-only and cannot become a live write path (ties to P2/invariant
  #1) before porting.

## ADAPTER — market-specific

- **`market_move_monitor.py` → `adapters/market/move_monitor.py`.** Pure (no DB/network),
  but market by design: detects sharp price moves on instruments from any feed via
  pluggable detectors. Correct home is the market adapter, **not** `engine/` — it is the
  textbook "market words live only in adapters" case (invariant #4). Note: its docstring
  mentions a Discord webhook alert sink in the *CLI wrapper* — that wrapper is out of scope
  here (no Discord work this pass); only the pure detector engine is the port target.

## REVIEW — decompose or decide before porting

- **`strategy_learning.py` (1894 LOC) — decompose, do not copy.** The inventory's named
  god-module. It mixes three concerns: (a) **concentration/exposure throttling**
  (`DEFAULT_STRATEGY_POLICY`, same-side / same-symbol multipliers) → `engine/` *as the
  concentration role only*; (b) receipt/state writes → `store/`; (c) policy/config (the
  strategy policy JSON) → `policy/` + `config/`. **Invariant #3 is the spec:** after the
  gate is the edge authority, strategy contributes **only concentration**, never edge.
  Port = carve (a) clean, leave the rest. Highest-effort item in the engine phase.
- **`paper_learning_epoch.py` (618) — analytics roll-up.** Reads outcomes, writes epoch
  summaries to `runtime_logs/`. Not core decision logic; likely becomes a curated tool or
  an analytics surface, not part of `engine/`. Decide its home when the tools keep-set is
  settled.
- **`live_trade_receipts.py` (435) — pin P2.** Live-execution-shaped table (`venue`,
  `leverage`, `opened/closed_at`, `source='operator_manual'`, `block_reason`). Almost
  certainly a **record-only** table for the allowed `manual_live_exposure_tracking` domain,
  but unconfirmed. **Decision required (P2):** port as a strictly read-only exposure record
  in `store/`, or leave it in the carried schema unused. It must **never** become a live
  write/execution path (invariant #1).

## CUT_ARCHIVE
None among the P3 modules — these are all load-bearing or decision-relevant. (The cut
clusters — `profit_*`, `announce_*`, rollout/branding one-offs — live in
`docs/foxclaw_v2_inventory.md` and stay in the v1-legacy archive.)

---

## Supplementary survey — gate + scoring (from `tools/`, surveyed 2026-06-17)

These two are NOT in GroveCore (so not in P3); the architecture port map sources them from
`tools/`. Both are read-only and pure-stdlib, but **neither is a drop-in engine port** — both
carry market vocabulary and need the same decompose-on-port treatment as `trustworthiness`.

### `tools/pre_decision_gate.py` → **REVIEW→split** → `engine/gate.py` + market adapter
- **Decision function it owns:** map a setup's `(score, n, trust_tier, freshness)` →
  a decision tier + commitment multiplier (`block 0 / reduce .5 / observe .75 / allow 1 /
  allow_boosted 1.2`), with a min-N guard (never boost on thin n) and a stale/missing-
  scoreboard safe fallback. Reads `config/setup_performance.json` (the scoreboard artifact).
- **Reads / must-not-write:** read-only; no DB, no orders. Keep that.
- **Invariant #4:** ⚠️ **leaks** — the setup key `source_id:symbol:side` and `long/short`
  are market framing; our `check_invariants.py` would (correctly) reject it in `engine/`.
  **Split:** the neutral tier/multiplier logic → `engine/gate.py` (keyed by an opaque
  arm/setup id); the `symbol:side` key construction → `adapters/market`.
- **Minimum tests:** tier→multiplier mapping; min-N suppresses boost→observe; block holds at
  any n; stale/missing scoreboard → safe `0.75` fallback; unknown setup → `0.75`.

### `tools/setup_performance_summary.py` → **REVIEW→split** → `engine/score.py` + adapter
- **Decision function it owns:** build the canonical per-setup scoreboard from
  `paper_outcomes` — win_rate / profit_factor / composite `score` / `trust_tier` / per-setup
  decision — with **corruption filtering** (`RETURN_SANITY_CAP`, entry-outlier vs symbol
  median) that *is* invariant #8 in code.
- **Reads / must-not-write:** read-only DB; writes only the JSON/MD scoreboard artifacts.
  ⚠️ hardcodes `data/grove_core.db` — on port it must use `store/db.resolve_db` (ties to P5).
- **Invariant #4:** ⚠️ heavy market vocab (trade, side, symbol, entry/exit, PnL). **Split:**
  the scoring math (`_score_setup`, `_trust_tier`, shrinkage) is neutral → `engine/score.py`;
  reading market outcomes + the corruption filters → `adapters/market` (or a store query).
- **Minimum tests:** score shrinks to 0.5 on small n; trust_tier thresholds; corruption
  filters drop impossible returns + entry outliers; catastrophe mean-return → block.

### ⚠️ Cross-cutting finding: the decision tier lives in THREE places
`block/reduce/observe/allow/allow_boosted` is defined independently in
`bayesian_edge.decision_label()`, in the scoreboard builder's per-setup `decision`, and in the
gate's mapping. That is three owners for one vocabulary — a latent "edge enters once"
(invariant #3) hazard at the code level. **One owner must be chosen on port.** Pinned as **P9**
in `docs/deferred.md`.

## Recommended Pass 2 scope (the actual port — a SEPARATE, later step)

Port the **pure trio** only, into `foxclaw/engine/`, tests-first, pure stdlib,
domain-neutral, no market hardwiring:

1. `engine/edge.py` ← `bayesian_edge.py` (verbatim-clean; it's already perfect altitude).
2. `engine/trust/reliability.py` ← `source_reliability.py` (diagnostic; not wired live).
3. `engine/trust/trustworthiness.py` ← `trustworthiness.py`, **splitting**
   `market_claim_well_formed` out to a minimal `adapters/market/` stub.

**Gate + scoring (now surveyed — see the supplementary section above):** both are read-only
and stdlib but **not drop-in** — each must be *decomposed* on port (neutral logic →
`engine/gate.py` / `engine/score.py`; market key/outcome handling → `adapters/market`).
Sequence them **after** the pure trio, and **resolve P9** (single owner of the decision-tier
vocabulary) as part of that work so the gate, the scoreboard, and `edge.decision_label` don't
re-create three competing tier definitions (invariant #3).

**Pass 3 (after Pass 2):** add the engine regression tests proving the chain
`evidence → edge estimate → gate decision → receipt-compatible output`, then bump to
**v0.2.0** with a CHANGELOG entry.

> **Update 2026-06-17 (Pass 2 tail done — v0.1.5):** the **neutral** halves of gate + scoring
> are ported and **P9 is resolved**. `engine/tiers.py` now owns the tier vocabulary +
> multipliers + boost-suppression; `engine/score.py` (trust_tier / composite_score /
> decision_tier) and `engine/gate.py` (the authority, keyed by an opaque subject) defer to it,
> as does `edge.decision_label`. The market `source:symbol:side` key moved to
> `adapters/market/setup.py`. 29 new unit tests (91 total green); invariant guard green over
> `engine/`. **Still owed for v0.2.0:** (1) the market scoreboard *builder* adapter — DB read +
> the corruption filters (`RETURN_SANITY_CAP`, entry-outlier vs symbol median = invariant #8)
> + the SQL, using `store/db.resolve_db` not the hardcoded `data/grove_core.db` (P5); (2) the
> Pass-3 regression test of the full chain.

---

See `docs/deferred.md` (P1, P2, P3), `docs/architecture.md` (target layout + port map),
and `docs/invariants.md` (#3 concentration-only, #4 domain-neutral, #5 ρ diagnostic,
#6 pure stdlib) for the rules this plan is bound by.
