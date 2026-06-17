# FoxClaw v2 — Clean Rebuild Plan

**Status:** planning · **Started:** 2026-06-17 · **Owner:** founder (Eastern Pine / FoxClaw)

## North star
Rebuild FoxClaw as a clean, professional, investor/buyer-ready system — **without losing
the asset that makes it valuable** (the auditable paper track record) and **without ever
stopping the live A2 organism.**

Locked decisions (2026-06-17):
- **Fresh `foxclaw-core` repo, curated history.** New clean repo; the current repo is
  archived private and linked for provenance (diligence sees clean code *and* a real past).
- **Two repos:** `foxclaw-core` (private engine) and `coinfox` (separate public surface).
- **Show-ready = polished demo as the headline, with an auditable track record + a clean
  professional codebase as non-negotiable foundations.** All three, demo on top.

## Non-negotiable guardrails (the rebuild must not violate these)
1. **The track record is the asset.** `data/grove_core.db` (paper history) is carried
   forward intact — schema + data. v2 is *new code around proven history*, not a restart.
   (invariant #8)
2. **A2 never stops.** The live paper loop keeps running on v1 throughout. v2 is built in
   parallel and only cuts over after shadow-validation on the same data. (invariant #2)
3. **Bake the doctrine in structurally**, not as conventions to re-discover: one edge
   authority (#3), share-nothing per-node stores (#9), local-first / vendor-neutral
   (no forced Microsoft/Google/vendor dependency), secrets only in `.env` (#7),
   domain-neutral core with market only in adapters (#4), pure-stdlib core (#6).

## Versioning & visible progress
- **Single source of truth:** the `VERSION` file at repo root (SemVer). Every FC-titled
  surface (cockpit, CoinFox, READMEs, demo headers) reads it — never hardcode a version.
- **Reset for v2:** starts at `0.1.0`. The pre-v2 system is frozen as the `v1-legacy`
  archive (its version is just that tag).
- **Cadence you can watch:** one **minor** bump per completed overhaul phase
  (`0.1 → 0.2 → …`); **patch** for small increments; **`1.0.0`** earned at A2 cutover when
  v2 runs the live track record and is demo-ready. Every bump gets a `CHANGELOG.md` entry.
- Titles read e.g. `FoxClaw v0.1.0 — Founder Cockpit`, so progress is visible everywhere.

## Current state (measured 2026-06-17)
- 1,480 tracked files · 1,057 Python · 482 test files.
- **`tools/` = 268 Python files — the cruft epicenter.** Obvious one-off clusters:
  `profit_*` (19), `post_grove_*` (7), `apply_*` (3), `announce_*`, `post_lynx_*`,
  `rollout_*`, `enforce_*`, `rename_*`, `generate_lynx*`, `setup_tradingview*`,
  `audit_grove*`, `discover_*`, `sync_discord*`.
- Real core is ~80 files: `src/` (39), `core/` (7), plus load-bearing `trading/app/*`.
- `docs/` = 257 files (heavily accumulated); `web/` = frontend (1 py); `scavenger/` (79 py,
  the intel listener) needs a keep-but-clean pass.

## Target: `foxclaw-core` layout (illustrative)
```
foxclaw-core/
  core/                 # domain-neutral engine — pure stdlib
    edge/               # bayesian_edge, scoreboard gate, source reliability
    intake/             # event capture -> parser -> candidate admission
    decision/           # gate, sizing, receipts
    trust/              # claim-contract / trustworthiness (diagnostic only)
    store/              # per-node sqlite + signed event log (share-nothing)
  adapters/
    market/             # the ONLY place market words live
    redshift/           # relay bridge + importer
    discord/            # intake source (thin)
  contract/             # the public contract CoinFox is allowed to consume
  tools/                # ~40 curated operator tools (cockpit, signal_flow_check, doctor)
  docs/                 # invariants, decisions, architecture, decision-math
  tests/                # the regression net that encodes the invariants
```
`coinfox/` is a separate repo that imports **only** `foxclaw-core/contract` — never internals.

## Phases

### Phase 0 — Freeze, inventory, scaffold
- Tag current repo `v1-legacy`, archive it private (the provenance link).
- Produce the **keep / cut / port** classification of all 1,057 py files (reviewable table).
- Stand up empty `foxclaw-core` and `coinfox` repos with curated initial history + CI skeleton.
- *Exit:* signed-off keep-list; two repos exist; v1 still running on A2.

### Phase 1 — Architecture & contracts
- Finalize the package layout above and the **public contract** CoinFox consumes.
- Pin the **carried-forward DB schema** as the stable asset boundary.
- Write `docs/architecture.md` (the diligence centerpiece).
- *Exit:* architecture + contract reviewed; DB schema frozen.

### Phase 2 — Carve the core (tests-first)
- Port the proven brain/gate/scoreboard/intake/grovecore into `core/`, bringing the
  regression tests that encode the invariants. Pure stdlib, domain-neutral.
- Drop the cruft (don't port `profit_*`, Discord/rollout one-offs, branding scripts).
- *Exit:* `foxclaw-core` runs the decision pipeline green on ported tests.

### Phase 3 — Carry the DB + shadow-validate on A2
- **Relocate the DB off any cloud-sync path first (invariant #9).** The live track record
  must live on a **local, non-synced** path — never OneDrive/Google-synced. v2 locates it
  vendor-neutrally via `$FOXCLAW_DB` (else `--db`, else repo-local `./data/grove_core.db`),
  so the move is config, not code. *Dev/A1 done 2026-06-17:* copied
  `OneDrive/Desktop/FoxClaw/data/grove_core.db` → `C:\Users\brend\foxclaw\data\grove_core.db`,
  `FOXCLAW_DB` set, schema guard green against the local copy. *A2 does the same at cutover:*
  copy to a local path, set `FOXCLAW_DB`, leave the OneDrive copy as a read-only fallback
  until parity is signed off, then retire it.
- Point v2 at the **same `grove_core.db`** (read-only first); run v2 in shadow beside v1.
- Prove parity: same inputs -> same edge/decision within tolerance (invariant #2).
- *Exit:* documented shadow parity report — the proof v2 is safe to lead; DB is off OneDrive.

### Phase 4 — CoinFox split
- Move CoinFox into its own repo; it consumes only the published contract.
- Public-safe by construction (no internals, no keys, no private DB).
- *Exit:* CoinFox builds against the contract; security boundary is structural.

### Phase 5 — Demo polish + diligence pack
- Demo: founder cockpit + CoinFox surface + live paper flow, professional UI.
- Diligence pack: `architecture.md`, **track-record proof** (the corruption-filtered
  scoreboard + receipts), clean README, test-coverage report.
- *Exit:* a click-through demo and a folder you can hand a buyer.

### Phase 6 — Cutover
- A2 runs v2 as primary; v1 archived read-only. Track record continues unbroken.

## The "cut in half" target
- `tools/` 268 -> ~40 curated operator tools.
- Drop/port classification owned in Phase 0; default-cut the one-off clusters above.
- Net expectation: well over 50% reduction in file count, with **more** capability
  surfaced cleanly (cockpit, signal-flow, doctor) and nothing load-bearing lost.

## Open questions for later phases
- Demo host: local-only cockpit vs a private hosted surface?
- `scavenger/` (79 py): keep as the intake listener, or fold into `core/intake`?
- How much of `docs/` (257 files) graduates into the curated repo vs stays in legacy archive?
