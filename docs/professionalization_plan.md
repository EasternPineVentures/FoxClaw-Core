# FoxClaw Professionalization — Grounded Against `foxclaw-core`

**Status:** reconciliation note · 2026-06-17 · **Read this before acting on any external
"professionalization plan."**

A professionalization plan was drafted (the "brilliant notebook → bound product" plan). It
is good in spirit and shares our doctrine — but **most of it was written against the v1 repo
(`OneDrive/Desktop/FoxClaw`), not this one.** Applied literally to `foxclaw-core` it would
either do nothing (work already done by construction) or contradict a locked decision. This
note records how it maps, so it is never pasted onto the wrong repo later.

> **The one-sentence guard:** `foxclaw-core` IS the cleaned-up product. The "archive the
> sprawl" surgery belongs to **v1** (which becomes the `v1-legacy` archive), not here.

## Verified state of THIS repo (2026-06-17)
`foxclaw-core` tracks only: `foxclaw/` (19), `docs/` (10), `tests/` (6), `config/` (2),
`tools/` (2), plus root metadata. Checked, and **none** of the plan's archival targets exist
here:

| Plan wants archived | In `foxclaw-core`? |
|---|---|
| `profit_*.py`, `announce_*.py` | ❌ not tracked |
| `trading/` , `scavenger/` , `web/` | ❌ not tracked |
| root-level `test_*.py` (~100) | ❌ not tracked (tests live in `tests/`) |
| `trading/app/main.py` (30k-line) | ❌ not tracked |
| stale `foxclaw.db` | ❌ not tracked (DB is gitignored + external via `$FOXCLAW_DB`) |

This is the curated-history rebuild working as designed (see
`docs/foxclaw_v2_overhaul_plan.md`, locked decision: "fresh repo, curated history; old repo
archived private as `v1-legacy`").

## How each part of the external plan maps here

| External plan item | Verdict for `foxclaw-core` |
|---|---|
| **Phase 1 — Repo Surgery** (archive legacy) | **N/A by design.** Done by construction; the archival, if any, is a *v1* task (tag it `v1-legacy`). |
| "✅ Bayesian edge / reliability / trustworthiness working" | **v1 only.** Here they are *surveyed, not ported* (`docs/engine_port_plan.md`, v0.2.0 Pass 2 target). |
| "✅ Apollo-1 understanding layer hardened" | **v1 only** (parked PR). Not in core. |
| Step 1: `git add core/understand.py … && git push` | **Does not apply.** Those paths don't exist here; and we commit locally, **no push**, by standing preference. |
| **Phase 2 — CI invariant enforcement** | ⭐ **Adopt — highest value.** Makes invariants structural (architecture.md already promises lint/CI). See dependency below. |
| `CONTRIBUTING.md` (city-planning doctrine) | **Adopt** — genuine gap (not present). |
| README one-pager / `getting_started.md` / `.env.example` | **Adopt** — small real polish. |
| "last reviewed" dates on `deferred.md` | **Adopt** — cheap anti-rot. |
| Makefile/justfile, devcontainer/Dockerfile, demo + proof report | **Defer** — these are the overhaul plan's later/Phase-5 work. |
| New `docs/professionalization_plan.md` + `docs/roadmap.md` + `docs/architecture_overview.md` | **Don't duplicate.** We already have `foxclaw_v2_overhaul_plan.md` + `architecture.md`. This file is the *reconciliation*; fold valid bits into the existing docs rather than spawning parallel roadmaps (the duplication trap). |

## Invariant numbering — use the real ones
The external plan renumbers the invariants. Any CI checks must reference the **canonical**
numbers in `docs/invariants.md`, not the plan's:

| External plan label | Canonical (`invariants.md`) |
|---|---|
| "paper-only" | **#1** |
| "no silent drift / edge enters once" | **#3** |
| "domain-neutral core" | **#4** |
| "pure stdlib" | **#6** |
| "no shared DB" | **#9** |

## Dependency that makes the good part honest
The plan's marquee item — a **#4 domain-neutral lint over `engine/` + `store/`** — **cannot be
switched on over `store/` today**: `store/outcomes.py` legitimately contains `realized_pnl_usd`,
`sharpe`, `long`/`short`. That is exactly **pin P1** in `docs/deferred.md` (where the
neutral-core/market line gets drawn). So:
- A **#6 pure-stdlib** lint over `engine/` and a **#9** DB-path/gitignore check can land now
  (both pass today).
- The **#4** lint must wait on the P1 decision (or be scoped to `engine/` only, where it
  passes). This is the pin doing its job — the guard rail forces the altitude call instead of
  letting it drift.

## Recommended adoption order (when we choose to act)
1. CI invariant guards: **#6 (engine pure-stdlib)** + **#9 (DB path/gitignore)** now;
   **#4** scoped to `engine/`, expanded to `store/` once P1 is resolved.
2. `CONTRIBUTING.md` — the city-planning doctrine (invariants, PR handoff, the pin ledger).
3. README one-pager + `getting_started.md` + `.env.example`.

None of this blocks the v0.2.0 engine port; it runs alongside.

---

See `docs/foxclaw_v2_overhaul_plan.md` (the canonical phase plan), `docs/architecture.md`
(target layout), `docs/engine_port_plan.md` (the engine survey), `docs/deferred.md` (pins,
incl. P1), and `docs/invariants.md` (canonical rules).
