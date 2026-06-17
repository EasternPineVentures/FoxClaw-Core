# FoxClaw v2 — Phase 0 Inventory & Keep/Cut/Port Classification

**Generated:** 2026-06-17 · Method: static import-graph analysis over 1,057 tracked `.py`
files (inbound-import counts + entry-point + orphan detection). Companion to
`docs/foxclaw_v2_overhaul_plan.md`.

> Top-down principle: this is not just "what to delete." Every workaround forced by the
> current layout is called out under **Layout scars** — v2 fixes the cause, not the symptom.

## Headline numbers
- **1,057 py files / ~278K LOC.** Test files: 482 (and **305 of them are stranded at the
  repo root**, not in `tests/`).
- **185 non-test orphans = 40,193 LOC with zero inbound imports.** `tools/` holds 134 of
  them (32K LOC) — half of `tools/` is one-off scripts.
- Real load-bearing core is small and identifiable (`src/grovecore/*`, `core/*`,
  a handful of `trading/app/*`).

## Load-bearing core (KEEP — port as the foundation)
Highest inbound-import counts = the spine the whole system leans on:

| Module | inbound | LOC | role |
|---|---|---|---|
| `src/grovecore/raw_events.py` | 67 | 397 | event intake record |
| `src/grovecore/parse_attempts.py` | 26 | 188 | parser audit |
| `src/grovecore/accepted_candidates.py` | 21 | 403 | candidate admission |
| `src/grovecore/paper_outcomes.py` | 19 | 810 | outcomes |
| `src/grovecore/paper_journal.py` | 18 | 462 | journal |
| `src/grovecore/decision_receipts.py` | 17 | 370 | receipts |
| `src/grovecore/bayesian_edge.py` | 11 | 393 | edge estimator (pure-Python) |
| `src/parsers/signal_parser.py` | 10 | 1,109 | parser (clean up on port) |
| `core/*` (gate/ingest/parse/score/paper/loop) | 20 (parse) | ~223 | **clean v2 skeleton already started** |
| `scavenger/app/core/*`, `providers/*` | 18–26 | small | intel listener spine |

**`src/grovecore/` is the crown jewel** — the receipt/decision data layer that produced the
track record. It ports almost as-is. **`core/` is a gift**: a small, clean,
domain-neutral skeleton (gate/ingest/parse/score) that looks like an earlier v2 attempt —
v2 should grow from here and absorb `grovecore` into it.

## Live process entry points (KEEP — orphan-by-import but run as processes)
These show 0 inbound imports but are **launched as services**, so they are NOT cut:
`trading/app/main.py`, `web/app.py`, `trading/app/user_ingest.py`,
`tools/financialjuice_monitor.py`, `tools/x_feed_monitor.py`,
`tools/chart_patterns_relay.py`, `tools/redshift_relay_watchdog.py`, the redshift
bridge/importer, `tools/foxclaw_doctor.py`, plus the two tools built this week
(`founder_cockpit.py`, `signal_flow_check.py`). Port + clean, don't delete.

## PORT-AND-CLEAN (load-bearing but must be refactored, never copied as-is)
| Module | LOC | problem | v2 action |
|---|---|---|---|
| `trading/app/founder_bridge.py` | 12,617 | god-module, inbound 69 | decompose into focused modules behind a thin facade |
| `trading/app/holdfast_capital.py` | 12,457 | god-module, inbound 54 | decompose; decide what is core vs adapter |
| `trading/app/command_center.py` | 3,884 | oversized orchestrator | slim to a coordinator |
| `lib/brain_v2.py`, `brain_v3.py`, `foxclaw_cortex.py`, `brain_enhancements.py` | — | **multiple brain generations coexisting** | collapse to ONE brain (invariant #3 made structural) |
| `trading/app/ohlcv_router.py`, `venue_matrix.py` | 734 / 501 | market logic in app | move to `adapters/market` |

## CUT-ARCHIVE (do not port — 134 tools/ orphans + others, ~40K LOC)
Default-cut clusters (one-off scripts, 0 inbound, not live processes):
- `tools/profit_*` (19), `post_grove_*` (7), `announce_*`, `post_lynx_*`, `rollout_*`,
  `apply_*`, `enforce_*`, `rename_*`, `generate_lynx*`, `setup_tradingview*`,
  `audit_grove*`, `discover_*`, `sync_discord*` — Discord/rollout/branding one-offs.
- Biggest individual orphans to drop: `tools/reality_audit.py` (3,416),
  `tools/algo_signal_bridge.py` (1,597), `tools/unresolved_context_radar.py` (1,027 — unless
  it graduates into the Context Intelligence Layer), `tools/polymarket_agent.py` (891),
  `tools/kalshi_event_scout.py` (726), `tools/ibkr_bridge.py` (579), `tools/decision_optimizer.py`,
  `tools/parser_intel_report.py`, dozens more.
- Archive (don't delete) in the `v1-legacy` repo so provenance survives diligence.

## Layout scars to fix top-down (the workarounds we no longer accept)
1. **305 test files at the repo root.** Move ALL into `tests/` with a real tree
   (`tests/unit`, `tests/regression`). This alone is the biggest professionalism win.
2. **Core logic fragmented across four homes** — `src/grovecore/`, `core/`, `lib/`,
   `trading/app/`. v2 has ONE core package; the rest are adapters or tools.
3. **God-modules** (`founder_bridge` 12.6K, `holdfast_capital` 12.5K) — decompose.
4. **Brain lineage sprawl** (`brain_v2`/`brain_v3`/`cortex`) — one brain, one edge.
5. **Duplicate names** (`founder_bridge.py` in both `tools/` and `trading/app/`) — namespace.
6. **Market words leaking into the core** — enforce domain-neutral core / market-in-adapters
   (invariant #4) structurally, with a lint check.
7. **`tools/` 268 → ~40** curated operator tools.

## Suggested keep-set size (the "cut in half" made concrete)
- Core: `src/grovecore` + `core` + `src/parsers` ≈ 50 files (clean).
- Adapters: market + redshift + discord intake ≈ 30 files (extracted from `trading/app`).
- Tools: ≈ 40 (cockpit, signal_flow, doctor, scoreboard builder, replay, the keepers).
- Tests: the invariant-encoding regressions, re-homed under `tests/`.
- **Net: ~1,057 → roughly 300–400 py files, with more capability surfaced cleanly.**

## Caveats
- Inbound-import is a proxy: a 0-inbound file can still be a live process (cross-checked
  above) or imported dynamically. Final cut on any ambiguous file = confirm it's not a
  running A2 process before archiving.
- `web/app.py` shows inbound 394 — inflated by the 305 root tests importing it; treat its
  real coupling as the dashboard, to be rebuilt as part of the demo surface.
