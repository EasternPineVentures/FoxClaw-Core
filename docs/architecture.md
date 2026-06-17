# FoxClaw Architecture (v2 / `foxclaw-core`)

**Status:** Phase 1 design · 2026-06-17 · companion to `foxclaw_v2_overhaul_plan.md` +
`foxclaw_v2_inventory.md`. This is the blueprint everything ports into.

## The key insight
The current `core/` package is a **facade**: `loop / gate / ingest / parse / score / paper`
already define the right clean surface, thin-wrapping proven implementations that today live
scattered in `tools/`, `src/`, and `trading/app/`. v2 **inverts the facade** — move the real
code *into* the package the surface already describes, and leave the god-modules behind. This
is a promotion of known-good code, not a risky rewrite.

## Layering (dependencies point inward only)
```
        adapters/  ─────────►  engine/  ─────────►  store/
       (market, redshift,     (pure stdlib,        (per-node sqlite,
        discord, news, llm)    domain-neutral)      signed event log)
                                   │
                                   ▼
                                policy/  (safety caps — the final veto)

        contract/  =  the ONLY surface coinfox (and any public node) may import.
```
Rules, enforced by lint/CI:
- **`engine/` is pure standard library and domain-neutral** (invariant #4, #6) — no
  market words, no numpy/scipy, no network. Market vocabulary lives only in `adapters/`.
- **Dependencies only point inward.** `adapters → engine → store/policy`. Nothing in
  `engine/` imports an adapter.
- **`store/` is per-node** (invariant #9). The shared substrate is a signed event log;
  the track record is derived and recomputable.
- **`contract/` is the airlock.** CoinFox imports `foxclaw.contract` and nothing else —
  never `engine`, `store`, `policy`, or `adapters`.

## Target package + port map
Each line shows the new home and `← where it comes from today`.
```
foxclaw-core/
  foxclaw/
    __init__.py              # __version__ reads VERSION
    loop.py                  # the single front door   ← core/loop.py
    engine/
      ingest.py              # raw events in, context-only filtered  ← tools/raw_parser.py (LiveRawParser)
      parse.py               # text -> structured plan  ← src/parsers/signal_parser.py (+ symbol_registry)
      score.py               # scoreboard build/refresh  ← tools/setup_performance_summary.py
      gate.py                # per-setup edge authority   ← tools/pre_decision_gate.py
      edge.py                # Bayesian edge estimator    ← src/grovecore/bayesian_edge.py
      decide.py              # candidate -> decision pass  ← trading/app/redshift_foxclaw_bridge.py
                             #                               (process_candidate_bridge, DECOMPOSED)
      trust.py              # trustworthiness / source reliability (DIAGNOSTIC only, invariant #5)
                             #   ← src/grovecore/trustworthiness.py, source_trust.py, source_reliability.py
    store/                   # the GroveCore data layer    ← src/grovecore/* (Store classes)
      events.py candidates.py decisions.py journal.py outcomes.py receipts.py ...
    policy/                  # safety caps & permissions   ← src/policy/*
      control.py             # FoxClawControl — hard veto  ← src/policy/foxclaw_control.py
      permissions.py decision_policy.py advisory_boundary.py
    adapters/
      market/                # OHLCV / venue / price       ← src/market_data/*, trading/app/ohlcv_router.py, venue_matrix.py
      redshift/              # relay bridge + importer      ← tools/redshift_foxclaw_bridge.py,
                             #                                trading/app/redshift_relay_importer.py, watchdog
      discord/               # community intake (thin)      ← trading/app/user_ingest.py (slimmed)
      news/                  # news classification          ← src/news/news_classifier.py
      llm/                   # LOCAL-FIRST advisory endpoint ← src/llm/compact_adviser.py
    contract/                # public surface for CoinFox / public nodes
      __init__.py            # published read-only views + types (see below)
  tools/                     # ~40 curated operator tools  ← founder_cockpit, signal_flow_check,
                             #   foxclaw_doctor, replay, scoreboard CLI (the keepers only)
  tests/
    unit/  regression/       # the 305 root test_*.py, re-homed and namespaced
  config/                    # foxclaw_control.json, sources.json, *.schema.json
  docs/                      # invariants, decisions, architecture, brain_decision_math
  VERSION  CHANGELOG.md  README.md  pyproject.toml
```
`coinfox/` is a **separate repo** that imports only `foxclaw.contract`.

## The public contract (`foxclaw.contract`)
The airlock between the private engine and any public surface. It exposes **read-only,
sanitized** views and the types to read them — never internals, keys, raw private data, or
write paths. Initial surface:
- `scoreboard_snapshot()` → public-safe per-setup performance (no private thresholds).
- `decision_receipt_view(id)` → a redacted, auditable receipt.
- `market_pulse()` / `source_memory_snapshot()` → context-only (report §2.2, §7).
- capability descriptor (`can_*: false` by default — authority granted deliberately).
Everything here is what the report's CoinFox layer is allowed to render. If it isn't in
`contract/`, CoinFox cannot reach it.

## Migration order (lowest-risk first)
1. **`store/`** — `src/grovecore/*` is already a clean package; it ports almost verbatim
   and carries the schema for the live `grove_core.db` (the asset, invariant #8).
2. **`engine/`** — bring `ingest/parse/score/gate/edge` (already isolated), then decompose
   `process_candidate_bridge` into `decide.py`. Tests-first, using the existing regressions.
3. **`policy/`** — `src/policy/*` moves with minimal change.
4. **`adapters/`** — extract market/redshift/discord/news/llm out of `tools/` and
   `trading/app/`, deleting the god-modules (`founder_bridge`, `holdfast_capital`) as their
   useful pieces are pulled forward.
5. **`contract/`** — define and freeze; wire CoinFox against it.
6. **`tools/` + `tests/`** — re-home the keepers and the test suite.

## How A2 stays live throughout (invariant #2)
v1 keeps running on Apollo 2 the entire time. v2 is built in the new repo and, once
`engine/` is green, runs in **shadow against the same `grove_core.db`** — same inputs must
yield the same edge/decision within tolerance. Only after a documented shadow-parity report
does A2 cut over to v2. Nothing live is touched until then.

## What "done with Phase 1" means (earns v0.2.0)
- [ ] This architecture reviewed/approved.
- [ ] `foxclaw.contract` surface agreed.
- [ ] `grove_core.db` schema frozen as the carried-forward asset boundary.
