# FoxClaw Invariants — the rules no agent may break

If you are an agent or contributor, read this **before** changing decision logic,
sizing, intake, or node behavior. These are not style preferences — breaking one
produces work that gets reverted (or worse, an unsafe system). Each rule says
*what*, *why*, and *where it lives* so you can verify you're respecting it.

When in doubt, leave a note in your PR's `Handoff / status` and ask. A wrong
assumption here is exactly how work gets "lost in transit" and cut later.

---

### 1. Paper-only. No live execution, ever, without an explicit separate grant.
FoxClaw cannot place a live order or move funds. Every receipt carries
`can_submit_orders=false`, `can_move_funds=false`. Listener/worker nodes hold
**no** money-moving credentials. Live capability is a separate, deliberate,
hard-gated grant — never a default, never a side effect of another change.
*Why:* safety is the whole license to operate. *Where:* `src/policy/foxclaw_control.py`, receipts everywhere.

### 2. Shadow-first. No live flip from theory.
New decision/sizing logic is **computed and logged but not wired to live sizing**
until it is validated against real history (a shadow tool comparing old vs new on
the *same* data). No estimator earns live influence from a clean idea alone.
*Why:* we caught real backfires only by shadowing (see `docs/source_reliability_math.md` Pass 3).

### 3. The edge enters `final` exactly once.
The scoreboard gate is the single per-setup edge authority. `defer_edge_to_gate`
guarantees: gate in shadow → the strategy layer applies the edge; gate active →
the gate applies it and strategy contributes only concentration. **Never both,
never zero.** `source_overrides` (`s_src`) is a ceiling — now `1.0` everywhere: as of
2026-06-16 the gate is **LIVE on A2** (`shadow=false`), so it is the single edge
authority and `defer_edge_to_gate` is true (strategy contributes only concentration).
*Why:* three layers multiplying the same edge is the bug we spent a week killing.
*Where:* `docs/brain_decision_math.md`, `redshift_foxclaw_bridge.py`, `strategy_learning.py`.

**Post-flip guard (the flip is done — keep it safe).** The gate went live and every
`source_overrides.*.paper_multiplier` is pinned to `1.0` (`neutralized_at_gate_flip`
stamped). This is now a standing invariant, not a one-time migration:
- *Detector:* `tools/founder_cockpit.py` reads `config/foxclaw_control.json` and raises
  **FAIL** on any `paper_multiplier != 1.0` — that is the double-throttle alarm. Treat a
  red Brain panel here as a stop-the-line event.
- *Rollback trigger — revert to gate `shadow=true` if any of:* a non-`1.0` override
  reappears; the scoreboard goes stale (cockpit Scoreboard-freshness WARN > 24h) while the
  gate is live and shaping size; or the gate is the sole authority but the scoreboard is
  missing/silent and the fallback recompute can't be confirmed.
- *Re-flip criteria (to go live again after a revert):* overrides confirmed `1.0`, a fresh
  scoreboard, and a shadow run showing the gate-applied edge matches the intended edge on the
  same data (invariant #2). Never re-flip from a clean idea alone.

### 4. The core stays domain-neutral.
The brain speaks **decision / category / arm / success / outcome / reward / cost /
commitment**. Never `trade / position / win / loss / PnL` in the core. Market
words live only in **adapters** (`trading/`). FoxClaw is a decision engine that
*has* a market adapter — not a trading bot.
*Why:* FoxClaw must generalize (markets, sourcing, content, business decisions).
*Where:* `docs/foxclaw_edge_engine.md`.

### 5. `ρ_source` weights evidence, never caps final size — and isn't folded into the edge yet.
Source reliability is an evidence weight (down-weight only, `ρ ∈ [floor, 1]`), not
a size multiplier or ceiling. And per the Pass-3 finding, **do not fold the current
outcome-rate `ρ` into the edge** — it relaxes blocks on unreliable sources.
Redefine `ρ` around *trustworthiness* first.
*Why:* keeps "edge enters once" alive and avoids re-creating `source_overrides`.
*Where:* `docs/source_reliability_math.md`.

### 6. The core is pure standard library.
`src/grovecore/` decision modules (edge estimator, source reliability, gate) use
**no numpy/scipy**. Heavy math libraries are fine in a research notebook, never in
the core, so it runs on every node.
*Why:* node portability; the Beta math is hand-rolled in `bayesian_edge.py` for this reason.

### 7. Secrets live only in a git-ignored `.env`.
Never commit a secret, token, API key, `.env`, the local DB, or runtime logs. A
secret scan runs in CI (`tools/secret_scan.py`) and over full history (gitleaks).
*Why:* the repo goes public eventually; history is forever. *Where:* `SECURITY.md`, `.gitleaks.toml`.

### 8. The track record is sacred — corruption-filter before trusting it.
`data/grove_core.db` (the decision/outcome history) is the irreplaceable asset.
Always corruption-filter before judging performance: drop impossible single-trade
returns (`RETURN_SANITY_CAP`) and mis-parsed entry-price outliers.
*Why:* a handful of corrupt rows once faked "negative expectancy" on a profitable system.
*Where:* `tools/setup_performance_summary.py`.

### 9. Node-local authoritative store; share-nothing.
Never treat a OneDrive-synced live DB as the shared source of truth across nodes —
that is a guaranteed-corruption cliff past one writer. The only shared substrate is
an append-only, **signed** event log; the track record is derived and recomputable.
*Why:* this is what lets the node network scale past ~10 without dying.
*Where:* `docs/node_network_architecture.md`.

### 10. Everything is an auditable receipt.
Decisions, and security-relevant events, leave a replayable receipt: why, inputs,
version, result. Prefer receipts over hidden magic.
*Why:* the brain must be auditable, correctable, and improvable by the next agent.

### 11. Public information only. No nonpublic, insider, hacked, classified, or private data.
FoxClaw estimates probability **only** from information that is lawfully public. It must
never form, score, or act on a forecast that depends on insider/material-nonpublic,
hacked/leaked, classified, or doxxed/private personal data. This is a hard input filter,
not a preference: an evidence source that smells nonpublic is rejected at intake, never
"used carefully." Applies everywhere, and especially to the **event-contract / Forecast
Desk** lane (Kalshi-first), where the temptation to trade on weird information is highest.
*Why:* the edge must come from better *reasoning over public evidence*, not from privileged
access — that is the only edge that is legal, durable, and shareable as a free signal.
*Where:* `foxclaw/adapters/event_contracts/` (dossier intake), `docs/forecast_desk_plan.md`.

### Event-contract hard locks (a corollary of #1, called out so it can't be missed).
Every `foxclaw/adapters/event_contracts/*` module is **read-only + paper-only**:
`can_submit_order=false`, `can_move_funds=false`, live eligibility **always false**, default
authority `A4_prohibited`. No account creation, no wallet/deposit, no live order routing, no
jurisdiction bypass, no LLM approval path. Venue expansion beyond Kalshi requires a separate,
founder-approved, venue-and-jurisdiction-specific review. *Why:* the Forecast Desk is an
intelligence lane, not an execution lane. *Where:* `docs/forecast_desk_plan.md` (pin P10).

---

See `docs/decisions.md` for *why* these are the way they are, and `AGENTS.md` for
*how* to work without losing context.
