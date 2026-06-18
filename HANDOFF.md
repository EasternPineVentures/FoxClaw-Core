# HANDOFF — the context football

> **What this is:** the running state of work on `foxclaw-core`, updated frequently so any
> session (or the founder on A2) can pick up cold without re-deriving context. Travels by
> **git** (invariant #9 — never OneDrive). When you resume: read this top-to-bottom first,
> then `git log --oneline -10`. When you stop: update the **Now / Next / Watch** block and
> the timestamp before you run out of juice.

**Last updated:** 2026-06-17 · **Branch:** `master` · **Version:** `0.2.0` · **Tests:** 117 green

---

## ▶ NOW (the active task) — FORECAST DESK (Kalshi-first, pin P10)

**Strategic pivot (2026-06-17):** the free signals now also cover **event-contract markets**,
hunting **mispriced probability** (Kalshi first). Same free signals, wider scope; capitalize on
the layers *around* them (sell/license the system · node-access tiers · future founder-gated live
op) — never by gating signals. Plan: `docs/forecast_desk_plan.md`. Business lens held throughout.

**Done (P10 Phase 0):** `foxclaw/adapters/event_contracts/` scaffolded, all hard-locked
(read-only/paper-only, live eligibility always false, A4_prohibited); `pricing.py` implemented
(the doctrine in code) + 17 tests. **Next phases, in order:**

1. **Phase 1** — `venues.py` (have Kalshi) → flesh `markets.py` (normalize public market catalog
   from already-fetched public data; no network in the pure layer) + keep `eligibility.py` deny-all.
2. **Phase 2** — `dossiers.py` (public-evidence packets; invariant #11 rejects nonpublic) +
   `pricing` (done) + `resolution.py` (settlement evidence).
3. **Phase 3** — `paper.py` (paper-only event receipts) + `tools/event_contract_scanner.py`
   (rank markets by edge gap) + a paper simulator.
4. **Phase 4** — `store/` `event_outcomes` table + `tools/forecast_scoreboard.py` (reuse
   `engine.score`, don't re-implement) + Founder Cockpit visibility.

> ⚠️ **Hard rails:** every `event_contracts/*` stays `can_submit_order=false` /
> `can_move_funds=false` / live-eligibility-false; public information only (invariant #11). Going
> live = a separate founder-approved authority grant, never a default.

**Parked (still real, lower priority than the Desk):** front-of-pipeline ingest/parse → decide
(v1 source `OneDrive/Desktop/FoxClaw/tools/raw_parser.py`), then shadow-parity vs A2 → v1.0.
⚠️ **A2 boundary (invariant #2):** A2 runs the live organism on v1 and must not stop; all build
work is on A1; cutover is a later deliberate step (pin P7).

## ✅ DONE — engine phase (v0.2.0)

- **P9 resolved:** `engine/tiers.py` is the single owner of the tier vocab + multipliers +
  boost-suppression. `edge.decision_label`, `engine/score`, `engine/gate` all defer to it.
- `engine/score.py` (neutral grader) + `engine/gate.py` (neutral authority, opaque subject).
- **Market scoreboard adapter** `adapters/market/scoreboard.py`: reads outcomes via the store
  (`get_closed_outcomes_with_source`), corruption filters (invariant #8), and the full chain
  `assess_setup` (outcomes → observations → edge → score-tier → gate-multiplier → verdict).
- 38 new tests across this + the prior pass; **100 total green**; invariant guard green.
- The complete decision spine now exists: `evidence → edge → gate → receipt-compatible output`.

## 👀 WATCH (don't trip these)

- **Invariant #4** — `engine/` stays domain-neutral. No symbol/side/long/short/PnL in
  `engine/`; the invariant guard (`check_invariants.py`) rejects it. Market words → adapters.
- **Invariant #6** — pure stdlib in `engine/` (no numpy/scipy).
- **Invariant #5** — ρ (trust/reliability) is diagnostic, weights-not-caps, NOT wired into
  live sizing without the shadow-first ritual.
- **Invariant #2** — A2 live organism never stops; this is A1 build work only. Don't touch A2.
- Run `python -m pytest -q` before committing; run the invariant guard over `engine/`.

---

## Where things are

- **Plan of record:** `docs/engine_port_plan.md` (per-module classification + port recipes).
- **Pins (deferred decisions):** `docs/deferred.md` — open: P1, P2, P4–P8 (P3 + P9 resolved).
- **Decisions already made:** `docs/decisions.md`.
- **Hard rules:** `docs/invariants.md`. **Target layout:** `docs/architecture.md`.
- **Phase plan:** `docs/foxclaw_v2_overhaul_plan.md`. **Keep/cut call:** `docs/foxclaw_v2_inventory.md`.
- **v1 source tree (read-only, OneDrive):** `OneDrive/Desktop/FoxClaw/{src/grovecore,tools}/`.

## Map of the rebuild (what's done)

- ✅ Scaffold + frozen DB schema (asset boundary, invariant #8).
- ✅ Store layer: decision receipt spine, paper execution (journal → outcomes), policy.
- ✅ Engine pure trio: `edge`, `trust/reliability`, `trust/trustworthiness`
  (+ market-claim split to `adapters/market/claims.py`).
- ✅ Engine gate + score (neutral) + P9 resolved (`engine/tiers.py`).
- ✅ Market scoreboard adapter + full chain (`assess_setup`) + regression → **v0.2.0**.
- ✅ Forecast Desk P10 Phase 0: `event_contracts/` scaffold + `pricing.py` (doctrine in code).
- ⏳ Forecast Desk Phases 1–4 (venues/markets → dossiers/resolution → paper → scoreboard)  ← **here**.
- ⬜ Parked: front-of-pipeline ingest/parse → decide; then shadow-parity → v1.0 at A2 cutover.

## Resume / stop checklist

**Resume:** read this file → `git log --oneline -10` → `python -m pytest -q` → open the NOW task.
**Stop (do before context runs out):** update NOW/NEXT/WATCH + timestamp/version/test-count
above → commit (`HANDOFF.md` included) so A2 / next session gets it via git.
