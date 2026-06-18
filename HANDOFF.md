# HANDOFF — the context football

> **What this is:** the running state of work on `foxclaw-core`, updated frequently so any
> session (or the founder on A2) can pick up cold without re-deriving context. Travels by
> **git** (invariant #9 — never OneDrive). When you resume: read this top-to-bottom first,
> then `git log --oneline -10`. When you stop: update the **Now / Next / Watch** block and
> the timestamp before you run out of juice.

**Last updated:** 2026-06-17 · **Branch:** `master` · **Version:** `0.2.0` · **Tests:** 100 green

---

## ▶ NOW (the active task)

**Engine phase is COMPLETE (v0.2.0).** The next phase is the **front of the pipeline**:
ingest / parse → decide, so live evidence can flow into the engine chain that now exists.

1. **ingest / parse** — port the v1 intake/parse path into `adapters/` + `store/` (raw events
   → parse attempts → accepted candidates → decision receipts). The receipt-spine store tables
   already exist; this is the producer side. v1 source: `OneDrive/Desktop/FoxClaw/tools/raw_parser.py`
   and the parse/candidate modules (survey first, like the engine port — classify before copying).
2. **decide** — the orchestrator that ties parse → `engine` (`adapters/market.assess_setup` is
   the reference chain) → a written decision receipt. This is where the brain runs a real input
   end to end.
3. Then **shadow-parity** against the live A2 `grove_core.db` (Phase 3) → v1.0 at cutover.

> ⚠️ **A2 boundary (invariant #2):** A2 runs the live organism on v1 and must not stop. All of
> the above is A1 build work; cutover is a later, deliberate step (pin P7).

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
- ⏳ ingest/parse → decide (front of the pipeline)  ← **you are here**.
- ⬜ shadow-parity against A2 `grove_core.db`, then v1.0 at A2 cutover.

## Resume / stop checklist

**Resume:** read this file → `git log --oneline -10` → `python -m pytest -q` → open the NOW task.
**Stop (do before context runs out):** update NOW/NEXT/WATCH + timestamp/version/test-count
above → commit (`HANDOFF.md` included) so A2 / next session gets it via git.
