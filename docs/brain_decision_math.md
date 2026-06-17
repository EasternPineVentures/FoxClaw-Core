# FoxClaw Brain — Decision & Sizing Math (v1)

A self-contained mathematical specification of how FoxClaw turns a parsed trade
signal into a paper position size. Written so an outside collaborator (quant,
researcher, or model) can verify or improve the logic **without reading the
codebase**. Every constant below is taken from live source as of 2026-06-15;
the file/line is cited so each can be checked.

> Scope: paper sizing only. Live trading is locked (`can_submit_orders=false`)
> everywhere. This is a *decision* spec, not an execution spec.

---

## 0. Objects & notation

- A **setup** is the triple `s = (source_id, symbol, side)`, e.g.
  `(coindesk_news, BTC/USD, short)`.
- For a setup with `n` closed paper trades we observe:
  - `w ∈ [0,1]` — win rate
  - `PF ≥ 0` — profit factor (gross profit / gross loss)
  - `r̄` — mean per-trade **return fraction** (size-independent; see §1)
  - `σ ∈ [0,1]` — composite score (defined in §2)
- A **proposal** is a candidate trade `(s, c)` where `c ∈ [0,1]` is the parser's
  raw confidence.

All money is USD. All trades are paper.

---

## 1. Return normalization (corruption-resistant input)

Raw PnL in $ is **not** used for scoring — it was contaminated by mis-parsed
entries (e.g. a $40k ETH fill). The score uses a size-independent return:

```
return(entry, exit, side) =  (exit − entry)/entry      if long
                             (entry − exit)/entry      if short
```
Filters before a trade counts toward a setup
(`setup_performance_summary.py:64,73`):
- `|return| > RETURN_SANITY_CAP = 1.0` (±100% in one trade) → dropped as corrupt.
- entry price `> 2×` or `< 0.5×` the symbol's median entry → dropped
  (`ENTRY_OUTLIER_RATIO = 2.0`, needs ≥4 entries for a trustworthy median).

> **Open problem A.** These are hard cutoffs. A robust estimator (e.g. winsorize
> at a percentile, or a heavy-tailed likelihood) may dominate hard thresholds.

---

## 2. Setup score `σ` (the edge estimator)

`setup_performance_summary.py:108`

```
raw(s)  = 0.5·w + 0.5·min(PF/3, 1)            ∈ [0,1]
λ(n)    = min(n / 30, 1)                       (Bayesian-style shrink weight)
σ(s)    = 0.5·(1 − λ(n)) + raw(s)·λ(n)         ∈ [0,1]
```

`σ` shrinks toward the neutral prior `0.5` when the sample is small; only at
`n ≥ 30` is `σ = raw`.

> **Open problem B (highest value).** `raw = 0.5w + 0.5·min(PF/3,1)` is an ad-hoc
> blend. Candidates an outside quant could compare against:
> - Wilson lower bound on `w` (penalizes small `n` with a proper interval),
> - Beta-Binomial posterior mean for `w`,
> - Expectancy / Kelly fraction `f* = (β·w − (1−w))/β` with `β` = avg win/avg loss,
> - a calibrated logistic on `(w, PF, n, r̄)`.
> Target property: `σ` is a *calibrated probability-of-edge* that is monotone in
> evidence and stable under manipulation.

---

## 3. Decision label `D(s)` (discrete verdict)

`setup_performance_summary.py:136`. Sample tiers: `LIGHT=3, TRUST=10, FULL=30`.

```
D(s) =
  observe                                    if n < 3
  block       if r̄ < −0.03 and n ≥ 3                 (catastrophe)
  block       if σ < 0.35   and n ≥ 10
  block       if r̄ < 0 and σ < 0.45 and n ≥ 10
  reduce      if σ < 0.45
  allow_boosted if σ ≥ 0.60 and n ≥ 10
  allow       otherwise
```
(evaluated top-to-bottom; first match wins)

---

## 4. Multiplier maps

### 4a. Gate multiplier `μ_g` — `PreDecisionGate` (`pre_decision_gate.py:56`)

```
μ_g(D) :  block 0.00 · reduce 0.50 · observe 0.75 · allow 1.00 ·
          allow_boosted 1.20 · unknown_setup 0.75 · stale 0.75
```
- `unknown_setup` = `s` absent from scoreboard. `stale` = scoreboard file older
  than `3600 s`, or missing.
- **Min-N guard:** if `D = allow_boosted` and `n < 5` → demote to `observe`
  (0.75). Never boost on a thin sample; a `block` always holds.

### 4b. Strategy edge multiplier `μ_s` — post-unification (`strategy_learning.py`)

Reads the **same** scoreboard through the **same** `PreDecisionGate`, then maps
conservatively (the strategy layer never boosts above 1.0):

```
μ_s(D) :  block → 0   ·  reduce → 0.5  ·  allow/allow_boosted → 1.0
          observe/unknown/stale → FALL BACK to legacy recompute g(·);
                                  if g(·) also silent → 1.0
```
`g(·)` is the old recent-window raw-PnL classifier, kept **only** as a safety net
for when the scoreboard cannot speak (missing / stale / unknown). When the
scoreboard speaks, `μ_s` uses it — so `μ_s` and `μ_g` can no longer disagree.

### 4c. Concentration multiplier `κ` (live open book) — *unique to strategy layer*

A throttle on the **current** open positions (not history). With open book of
size `N`, side count `k` for the proposal's side, ratio `ρ = k/N`:

```
κ_side  = clamp(   max_mult − (max_mult − min_mult)·(ρ − ρ_t)/(ρ_full − ρ_t)  )
          when ρ > ρ_t   (defaults ρ_t=0.55, ρ_full=0.85, min=0.2, max=1.0)
κ_sym   = max( min_mult , 1/(setup_count+1) )   for repeated same symbol+side
κ       = the binding (smaller) of the applicable terms, else 1.0
```
`κ ∈ (0,1]` — can only reduce. This is the **only** cross-trade term in the
system.

---

## 5. Full sizing pipeline (three stages)

Constants (`config/foxclaw_control.json`): `b₀ = base_notional_usd = 100`,
`confidence_scaling = false ⇒ φ(c) = 1`, `C = max_single_paper_notional_usd = 100`.

```
Stage 1 (base)        b         = b₀ · φ(c)                     = 100
Stage 2 (bridge)      requested = b · m_strategy · m_gate
Stage 3 (control cap) final     = min( requested , C · s_src )
```
where
```
m_gate     = 1                       if gate in shadow
             μ_g(D(s))               if gate active
m_strategy = κ                       if defer_edge_to_gate  (gate active)
             min( μ_s(D(s)) , κ )    otherwise              (gate shadow)
s_src      = source_override.paper_multiplier ∈ [0,1]   (per source_id)
```
and `final = 0` (**trade dropped**) if any hard block fires:
- shadow: `μ_s` resolves to `block`
- active: `D(s) = block` at the gate
- control result `∉ {allow, shadow_allow}`

### The composition wrinkle (verified, important)

Stage 2 is a **product**; Stage 3 is a **min-ceiling**. With `b = C = 100`:

```
final = 100 · min( m_strategy · m_gate ,  s_src )
```

So `s_src` behaves as a **hard cap that only binds when** `m_strategy·m_gate > s_src`.
This is why a stale `s_src = 0.4746` caps an *allowed* setup (`m = 1`) down to
`$47.46` — the "double penalty." `brain_audit.py`'s `net = gate × override`
column is therefore an **approximation**; the true value is the `min` above.

---

## 6. The invariant we are enforcing (the unification)

Define the **edge** of a setup `E(s) := μ(D(s))` (its scoreboard verdict).
Correctness requires `E` enter `final` **exactly once**:

| regime | edge applied via | proof |
|---|---|---|
| gate **shadow** | `m_strategy` (`m_gate = 1`) | `defer=false ⇒ m_strategy = min(μ_s, κ)` |
| gate **active** | `m_gate` (`m_strategy = κ`) | `defer=true ⇒ edge dropped from m_strategy` |

Never `E²`. The boolean `defer_edge_to_gate = (gate enabled ∧ ¬shadow)` is what
guarantees this. **Target end-state:** when the gate flips active, set
`s_src = 1 ∀ source` so Stage 3 stops re-throttling — the gate `μ_g` is then the
single edge authority, `m_strategy = κ` (concentration only), `s_src = 1`.

---

## 7. Open problems for outside help (ranked)

1. **Score `σ` (Open B).** Replace the ad-hoc blend with a calibrated
   probability-of-edge robust at small `n`. This is the single highest-leverage
   change — every multiplier downstream inherits its quality.
2. **Continuous sizing `μ(σ)`.** The discrete map `{0, 0.5, 0.75, 1, 1.2}` is
   heuristic. Should size `∝` fractional Kelly `f*(σ)` with a safety factor,
   giving a smooth monotone `μ(σ)`?
3. **Clean composition.** Make Stage 3 a multiplier (`final = b·∏ mᵢ`) instead of
   a `min`-ceiling, removing the wrinkle in §5 and making the whole pipeline a
   single analyzable product.
4. **Sample → trust.** `3 / 10 / 30` and min-N `5` are guesses. What interval
   width (Wilson / Bayesian) actually justifies "trust"?
5. **Manipulation resistance.** Thesis: *"if it's on the web it can be
   manipulated."* Model a per-source reliability `ρ_source ∈ [0,1]` (agreement of
   the source's signals with realized outcomes) and fold it in as a weight — a
   principled replacement for the hand-set `source_overrides`.
6. **Portfolio term.** Sizing is per-setup independent; `κ` is the only
   cross-trade coupling. Is a correlation / portfolio-variance term warranted?

---

## 8. Reproduce / verify the live numbers

```
python tools/setup_performance_summary.py            # rebuild scoreboard (σ, D per setup)
python tools/pre_decision_gate.py --source coindesk_news --symbol BTC/USD --side short --confidence 0.65
python tools/brain_audit.py                          # gate vs source_override (net is approximate — see §5)
python tools/refresh_source_overrides.py             # dry run: source_overrides vs scoreboard
```

Canonical scoreboard: `config/setup_performance.json`. Control/overrides:
`config/foxclaw_control.json`. Pipeline code: `redshift_foxclaw_bridge.py`
(Stage 2), `src/policy/foxclaw_control.py:438` (Stage 3),
`src/grovecore/strategy_learning.py` (`μ_s`, `κ`).
