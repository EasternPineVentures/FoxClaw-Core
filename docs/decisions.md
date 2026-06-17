# FoxClaw Decision Log

Short, dated records of the load-bearing decisions and *why* — so no agent has to
re-derive them, and no one silently reverses a choice without seeing the reasoning.
If you're about to do the opposite of one of these, that's fine — but say why in
your PR, and update the relevant entry. (Append-only in spirit; supersede, don't delete.)

Format: **what** · why · consequences. Newest first.

---

### 2026-06-16 · Boost suspicion RESOLVED — the 1.2× boost earns its keep
**Finding (`tools/gate_multiplier_analysis.py`):** investigated the gate_discrimination
hint that `allow_boosted` underperformed `allow`. Walk-forward, varying the boost
multiplier: boost=1.2 → 2.5998, boost=1.1 → 2.4135, boost=1.0 (no boost) → 2.2272.
**Higher boost = higher out-of-sample return, robust at both splits.** The earlier
"boost suspect" flag was a red herring. **Key insight:** per-tier mean return (does the
gate ORDER correctly?) and sizing value (do the multiplier MAGNITUDES pay?) are
different questions — `allow_boosted` has a lower per-trade mean than `allow` but is
still net-positive, so sizing it up still adds return. `observe` is moot (walk-forward
produces no observe decisions at min_train≥5). **Decision:** keep the live gate
multipliers (incl. 1.2× boost). The post-flip `--since-days` watch continues as the
real-data check. Supersedes the "watch the boost" item.

### 2026-06-16 · Gate discrimination: it sizes losers down / winners up; boost tier is suspect
**Finding (`tools/gate_discrimination.py`):** walk-forward, bucket realized return by
the gate tier the decision would land in. The gate **discriminates at the gross
level** — `block`/`reduce` realized NEGATIVE mean returns (~−0.001/−0.003, <30% win)
while `allow`/`allow_boosted` were POSITIVE (~+0.010/+0.006, ~50%+ win). The core
thesis (size losers down, winners up) holds. **But** `allow_boosted` (the 1.2× boost,
n=316) realized *less* than plain `allow` (+0.006 vs +0.010, n=39) — the boost may be
mis-targeted. Caveat: `allow` is small-sample (n=39) so the inversion may be noise.
**Decision:** watch it post-flip with `--since-days`; if the boost-underperforms-allow
inversion persists on fresh data, revisit the `allow_boosted` threshold (σ≥0.60) or the
1.2× boost. No change now. Doubles as the live post-flip discrimination watch.

### 2026-06-16 · GATE IS LIVE on A2 — scoreboard gate activated (coupled flip applied)
**Event:** the operator ran `python tools/gate_flip.py --apply` on **A2**. Pre-flight
passed (scoreboard fresh ~407s, 8 decisive setups, 2 contradictions). The coupled
flip set `scoreboard_gate.shadow = false` AND every `source_overrides[*].paper_multiplier
= 1.0` atomically (coindesk 0.4746→1.0, financialjuice 0.5→1.0, x_social 0.5→1.0),
verified, backup `foxclaw_control.bak_20260616T085026Z.json`. **Consequence:** the brain
is now in its coherent ACTIVE state on A2 — the **scoreboard gate is the single edge
authority** (block 0 / reduce .5 / observe .75 / allow 1 / boost 1.2), `strategy_learning`
defers the edge and adds only concentration, `s_src = 1.0`. Live paper sizing changed
(observe/unknown setups now size 0.75; blocks block). Evidence it beats σ out-of-sample:
the walk-forward backtest above. **Still paper-only.** Rollback: restore the backup on A2.
This Desktop checkout (A1) was NOT flipped — only A2 is live.

### 2026-06-16 · Hyperparameter sensitivity: keep the defaults; stronger prior is a shadow-trial candidate
**Finding:** `tools/edge_tune.py` sweeps (prior_strength, half_life, risk_aversion)
using the walk-forward backtest as a fitness function, with a robustness re-check at
a second `min_train`. Results: (a) the method is **robustly insensitive** — all 18
configs cluster within ~1%; (b) a **stronger prior** (`prior_strength` 4–8, i.e. the
originally-intended skeptical α=β≥2) is *modestly* better and holds at both splits;
(c) `risk_aversion` is **nearly inert under `min`** (the min is usually bound by the
probability mapping, so the Kelly haircut rarely binds). **Decision:** do NOT change
the live default off one history (the gain is ~1%, the engine is shadow-only, and
single-history tuning is the overfitting trap). Logged `prior_strength≈4` as a
shadow-trial candidate for the eventual live config. **Consequences:** defaults stay
`prior=2, no decay, risk_av=0.25`; revisit under multi-history/walk-forward before any change.

### 2026-06-16 · Walk-forward evidence: the Bayesian edge beats σ out-of-sample (modestly)
**Decision/finding:** `tools/edge_backtest.py` runs a walk-forward (no-lookahead)
backtest on the real track record. Across 380-440 out-of-sample decisions and
`min_train` ∈ {3,5,8,12} (±recency), **new (prob) > old σ > flat** in every
configuration. All sizing beats flat (past edge persists); the new Bayesian
estimator sizes a bit better than σ. **Be honest:** the margin over σ is *modest and
narrows as data grows* (near-tie at min_train=12); the large win is sizing-vs-flat
(~30-40%). `new_min` trails `new_prob` slightly (the conservative veto costs a little
return for safety). **Consequences:** this is the "cage match" replay proof the
promotion path required — evidence to support eventually flipping the gate, still
under the shadow-first + coupled-flip discipline. No live change made.

### 2026-06-15 · Source scoring is ONE domain-neutral substrate; context stays context-only
**Decision:** signal reliability (`ρ_source`), trustworthiness (`ρ_trust`), and A2's
context **Source Memory Layer** all reuse the one domain-neutral Beta-reliability
substrate (`src/grovecore/source_reliability.py` / `trustworthiness.py`) — not a
parallel scorer. The Context Intelligence Layer is `context_only` and never becomes a
trade/confidence input except through the normal reviewed parser/gate front door.
**Why:** two streams (A2 intake + the brain) were converging on "source scoring";
parallel systems are the duplicated work we keep having to cut. **Consequences:** see
`docs/context_intelligence_boundary.md`.

### 2026-06-15 · Multi-agent coordination via AGENTS.md
**Decision:** every in-flight branch has a Draft PR with a `Handoff / status` note;
ownership-prefixed branches; a stale bot surfaces (never deletes) idle work.
**Why:** a graveyard of abandoned `codex/*` branches had formed — work lost in
transit. **Consequences:** `AGENTS.md` is the entry point; no hidden branches.

### 2026-06-15 · Shared in-repo context (this log + `docs/invariants.md`)
**Decision:** the "why" and the hard rules live in the repo, not only in one agent's
private memory. **Why:** Codex/Copilot can't read Claude's memory; un-shared context
is how an agent lands in a weird spot and builds something we cut later.
**Consequences:** agents read `invariants.md` + this log before changing core logic.

### 2026-06-15 · Repo stays private until CoinFox; public gated on a clean history scan
**Decision:** build the open-source structure now (AGPL, CI, templates) but flip to
public only after CoinFox ships and a full gitleaks history scan is clean.
**Why:** going public exposes all history; do it deliberately. **Consequences:**
history verified clean (only fake test placeholders + public contract addresses).

### 2026-06-15 · License: AGPL-3.0
**Decision:** AGPL-3.0 for the open core. **Why:** keeps the core open even when run
as a network service (share-back), fitting the free/community thesis while CoinFox
stays a separate commercial layer. **Consequences:** contributors agree to AGPL; some
companies avoid AGPL deps (accepted trade-off).

### 2026-06-15 · `ρ_source` is a diagnostic, not (yet) an edge input
**Decision:** ship source reliability as a shadow diagnostic; do **not** fold the
outcome-rate `ρ` into the edge. **Why:** the Pass-3 shadow showed naive folding
*relaxes* blocks on unreliable sources and conflates hit-rate with edge.
**Consequences:** redefine `ρ` around trustworthiness (direction/level/manipulation)
before it influences sizing. See `docs/source_reliability_math.md`.

### 2026-06-15 · Combined commitment = `min(prob, kelly)`
**Decision:** default commitment is `min(commitment_prob, commitment_kelly)`.
**Why:** "probability must like it AND Kelly must not hate it" — neither a confident-
but-tiny edge nor a fat-but-uncertain one can size up alone. **Consequences:** more
conservative default; both components still exposed for shadow comparison.

### 2026-06-15 · CI runs a pure-stdlib core suite, not the full monorepo deps
**Decision:** CI installs only `pytest` and runs the core decision-engine tests.
**Why:** the full `requirements.txt` includes Python-3.13-only packages that break a
3.11 install; the core is pure-stdlib anyway. **Consequences:** fast, reliable PR
signal; run the full suite locally.

### ~2026-06-14 · The brain has one edge authority ("edge enters once")
**Decision:** unify three contradictory sizing layers onto the scoreboard gate;
`strategy_learning` consumes the gate, `source_overrides` neutralize to 1.0 when the
gate goes active. **Why:** the layers double/triple-counted the same edge and fought
each other. **Consequences:** `defer_edge_to_gate` enforces single application. See
`docs/brain_decision_math.md`.

### ~2026-06-14 · Adopt a Bayesian edge estimator, domain-neutral, pure-Python
**Decision:** replace the ad-hoc score `σ` with `P(edge) = P(EV>0)` via a
Beta-Binomial posterior + conservative Kelly, all domain-neutral and stdlib-only.
**Why:** a calibrated, explainable, portable estimator that generalizes beyond
markets. **Consequences:** no numpy/scipy in core; market terms stay in adapters.

### ~2026-06-13 · Shadow-first promotion discipline
**Decision:** new decision logic runs in shadow and is compared on the same data
before any live flip; `source_overrides` neutralization is coupled to the gate flip.
**Why:** theory backfires in practice; we only catch it by shadowing.
**Consequences:** nothing sizes live from an idea alone.

### ~2026-06-13 · FoxClaw is a domain-neutral decision engine (paper-only)
**Decision:** the core is a general "does this category of action have positive
expected value, and how hard to commit" engine; markets are one adapter; it never
trades live. **Why:** the project must grow beyond crypto (sourcing, content,
business) and stay safe. **Consequences:** the domain-neutral + paper-only invariants.

---

See `docs/invariants.md` for the rules these decisions produced, and `AGENTS.md` for
how to work without losing context.
