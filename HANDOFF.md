# HANDOFF — the context football

> **What this is:** the running state of work on `foxclaw-core`, updated frequently so any
> session (or the founder on A2) can pick up cold without re-deriving context. Travels by
> **git** (invariant #9 — never OneDrive). When you resume: read this top-to-bottom first,
> then `git log --oneline -10`. When you stop: update the **Now / Next / Watch** block and
> the timestamp before you run out of juice.

**Last updated:** 2026-06-17 · **Branch:** `master` · **Version:** `0.1.5` · **Tests:** 91 green
**Uncommitted:** yes — the gate+score+P9 port is staged in the working tree, not yet committed.

---

## ▶ NOW (the active task)

**Engine port — finish Pass 2 / start Pass 3.** The neutral gate + scoring + P9 are DONE in the
working tree (see below). Remaining to earn **v0.2.0**:

1. **Market scoreboard *builder* adapter** — port the DB-reading half of v1
   `tools/setup_performance_summary.py` to `adapters/market/scoreboard.py`: read paper_outcomes
   (prefer via `store/`), apply the **corruption filters** (`RETURN_SANITY_CAP`,
   entry-outlier-vs-symbol-median = **invariant #8 in code**), build the `setup_key`, compute
   success_rate/reward_factor/mean_reward, and call `engine.score`. Use `store/db.resolve_db`,
   **not** hardcoded `data/grove_core.db` (P5). Needs a fixture DB to test.
2. **Pass-3 regression test** — prove the chain `evidence → edge → gate → receipt-compatible
   output` end to end.
3. Bump **v0.2.0** + CHANGELOG.

> Source (v1, read-only): `OneDrive/Desktop/FoxClaw/tools/setup_performance_summary.py`
> (the `build_scoreboard` / `_return_fraction` / corruption-filter half — the scoring math
> `_score_setup`/`_trust_tier`/`_decision_label` is already ported to `engine/score.py`).

## ✅ DONE THIS PASS (uncommitted, v0.1.5)

- **P9 resolved:** `engine/tiers.py` is the single owner of the tier vocab + multipliers +
  boost-suppression. `edge.decision_label`, `engine/score`, `engine/gate` all defer to it.
- `engine/score.py` (neutral grader), `engine/gate.py` (neutral authority, opaque subject),
  `adapters/market/setup.py` (the `source:symbol:side` key).
- 29 new tests (`tests/unit/test_gate_score.py`); 91 total green; invariant guard green.
- Docs updated: `decisions.md` (P9 RESOLVED), `deferred.md` (P9 struck), `engine_port_plan.md`,
  CHANGELOG, VERSION→0.1.5.
- **Next action if resuming:** `git add -A && git commit` this, then start the builder adapter.

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
- **Pins (deferred decisions):** `docs/deferred.md` — open: P1, P2, P4–P9.
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
- ⏳ Market scoreboard *builder* adapter + Pass-3 regression → v0.2.0  ← **you are here**.
- ⬜ ingest/parse, decide (full engine chain), then shadow-parity → v1.0 at A2 cutover.

## Resume / stop checklist

**Resume:** read this file → `git log --oneline -10` → `python -m pytest -q` → open the NOW task.
**Stop (do before context runs out):** update NOW/NEXT/WATCH + timestamp/version/test-count
above → commit (`HANDOFF.md` included) so A2 / next session gets it via git.
