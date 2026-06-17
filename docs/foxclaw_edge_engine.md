# FoxClaw Edge Engine — the domain-neutral doctrine

> **FoxClaw is a receipt-driven adaptive decision engine. It watches source
> claims, turns them into structured proposals, estimates edge from replayable
> outcomes, sizes commitment under uncertainty, gates authority, and records
> every decision so the brain can be audited, corrected, and improved.**

FoxClaw is **not** a trading bot. It is a decision engine that *currently has a
market adapter*. The core must never be tattooed with "trading" — the same math
sizes a trade, a sneaker flip, a card buy, a content test, a research source, or
an agent recommendation. Market words live in adapters, not in the brain.

This document is the canonical wording + math for the **Edge Engine**
(`src/grovecore/bayesian_edge.py`). It is written to be handed to an outside
quant or model without the codebase.

---

## 1. Vocabulary — say it domain-neutral

| Market word (adapter only) | Core word (the brain speaks this) |
|---|---|
| trade | decision / action |
| setup | decision category / arm |
| signal | input event / source claim |
| win / loss | successful / unsuccessful outcome |
| profit / loss amount | reward / cost |
| PnL | outcome value |
| position size | commitment |
| bankroll | risk budget |
| source / trader | source / analyst / agent / node |
| backtest | replay / historical validation |
| trading strategy | decision policy |
| market regime | environment state |
| paper trade | simulated action |
| live trade | external action with real-world consequence |

---

## 2. Object model

```
A decision category ("arm") is a repeatable pattern of action.
An observation is one past action with an outcome:
    success   ∈ {0,1}
    magnitude > 0          # reward if success, cost if not (fraction of stake)
    age       ≥ 0          # how long ago, for recency weighting
    source                 # who produced the claim (future: reliability weight)
    context                # tags (future: environment state)
```

Markets, flips, content tests, research sources are all just **adapters** that
emit `Observation(success, magnitude, age)`.

---

## 3. The edge estimate (replaces the ad-hoc σ)

For an arm's success probability `p` with reward `r` and cost `c`:

```
EV = p·r − (1−p)·c            (expected outcome value)
EV > 0   ⇔   p > c / (r + c)  (positive-edge threshold)
```

With a Beta prior and (optionally recency/reliability-weighted) evidence:

```
p | data ~ Beta(α₀ + S_eff, β₀ + F_eff)
P(edge)  = P(p > c/(r+c)) = 1 − BetaCDF( c/(r+c), α₀+S_eff, β₀+F_eff )
```

This single quantity already folds in success rate, payoff asymmetry, sample
size, and uncertainty — no separate profit-factor patch needed. It **replaces**:

```
σ = 0.5(1−λ) + (0.5w + 0.5·min(PF/3,1))·λ ,  λ = min(n/30,1)
```

`r` and `c` are **shrunk, tail-aware** estimates: a robust mean (NOT the median —
the median hides the rare large losses that decide whether an arm is really
net-positive), shrunk toward a domain reference when the arm is thin. Corruption
is filtered upstream by the adapter; the engine assumes its inputs are clean.

---

## 4. Commitment sizing (with a seatbelt)

Two transparent maps into the multiplier `m ∈ [0, max_commitment]` (default 1.2):

```
m_prob  = clamp( 2.4·(P(edge) − 0.5), 0, 1.2 )         # interpretable
m_kelly = clamp( (kelly/kelly_cap)·1.2, 0, 1.2 )       # conservative Kelly
```

where the Kelly fraction uses a **lower posterior quantile** of `p` (25th
percentile) and a fractional-Kelly haircut, so one lucky streak can't size up:

```
p_safe = BetaPPF(0.25, α₀+S_eff, β₀+F_eff)
kelly  = clamp( risk_aversion · (p_safe·r − (1−p_safe)·c)/(r·c), 0, kelly_cap )
```

Default and recommended composition — **`m = min(m_prob, m_kelly)`**: probability
must like it *and* Kelly must not hate it. Neither a confident-but-tiny edge nor a
fat-payoff-but-uncertain arm can size up alone.

**Exploration floor + claws:**
```
if n_eff < min_observations and not catastrophic:   m = max(m, exploration_floor)
if n_eff ≥ 3 and conservative_EV < catastrophe:     m = 0
```
Curiosity for unknowns; claws for obvious danger. A learning system that zeros
every unknown can never learn a new arm.

Defaults: `prior_strength=2, risk_aversion=0.25, kelly_cap=0.25,
max_commitment=1.2, min_observations=5, catastrophe=−0.03`.

---

## 5. How the Edge Engine plugs into the brain

The verified live sizing pipeline (market adapter):
```
final = C · min( m_strategy · m_gate , s_src )         (b = C = 100 today)
```
- **One edge, applied once** — the invariant. Edge `E = μ(decision)` enters
  `final` exactly once: in shadow via `m_strategy`, when the gate is active via
  `m_gate` (`defer_edge_to_gate`), never both.
- `s_src` (source override) is a **ceiling** (`min`), not a chain multiplier.
- **Clean active end-state:** `s_src = 1` for all sources, `m_strategy = κ`
  (concentration only), `m_gate = μ_g(decision)` → `final = C · κ · μ_g`.

The Edge Engine produces the `decision` and the commitment; the gate applies it;
concentration `κ` can only tighten; receipts record the why.

---

## 6. Planned next: source reliability (retire `source_overrides`)

Replace the hand-set, stale `source_overrides` with a **living reliability term**
`ρ_source ∈ [0,1]` (how well a source's claims have matched realized outcomes),
folded into evidence weight rather than bolted on as a ceiling:

```
w_i   = 2^(−age_i / H) · ρ_source · q_i
S_eff = Σ w_i over successes ,  F_eff = Σ w_i over failures
```

A poisoned source then doesn't just get "blocked" — its future observations
naturally count less until it re-earns trust. This is the manipulation-resistant
answer ("if it's on the web it can be manipulated") and pairs with the
share-nothing, signed-event-log node architecture where every score is derived
and recomputable.

---

## 7. Outside-help brief (hand this to a quant/model)

```
FoxClaw is a domain-neutral adaptive decision engine. For each repeatable
decision category we observe outcomes: success/failure, reward magnitude, cost
magnitude, age, source identity, context tags.

Replace the current ad-hoc score
    σ = 0.5(1−λ) + (0.5w + 0.5·min(PF/3,1))·λ ,  λ = min(n/30,1)
with a calibrated probability of positive expected value
    P(edge) = P(p·reward − (1−p)·cost > 0 | observations)
using a Beta-Binomial posterior for p and robust/shrunken reward & cost.
Output a commitment multiplier m ∈ [0,1.2] that is monotone in evidence,
conservative at small n, robust to outliers, exploration-compatible,
explainable in receipts, and replayable from append-only observations.

Open questions:
 1. prior strength?
 2. reward/cost estimator: mean, winsorized/Huberized mean, or hierarchical shrinkage?
 3. which posterior quantile drives commitment?
 4. how to apply time decay?
 5. how should source reliability enter?
 6. commitment via P(edge), fractional Kelly, or min(both)?
 7. how to calibrate P(edge) vs future outcomes (calibration curve / Brier / log-loss / walk-forward)?
```

---

## 8. Promotion discipline (no live flip from theory)

```
1. shadow only (tools/bayesian_edge_shadow.py) — recompute old σ AND new P(edge)
   from the SAME observation set (never stale-JSON vs fresh-DB)
2. compare disagreements for 1–2 weeks
3. calibrate (calibration curve, Brier, walk-forward)
4. pick hyperparameters by multi-objective validation (NOT raw PnL)
5. update scoreboard schema
6. gate stays the single edge authority
7. source_overrides neutralized only AT the gate flip, never before
```

No performance-lift claim is made until replay proves it. The math earns its
place in a cage match against history first.

---

## What is already built vs. next

**Built (shadow-only, tested):** the domain-neutral `BayesianEdge`
(`success/magnitude/age`, pure-Python Beta CDF/PPF — no numpy/scipy), `P(edge)`,
conservative Kelly, `min(prob,kelly)` commitment, exploration floor + catastrophe
block, tail-aware mean, and `bayesian_edge_shadow.py` with same-observation-set
comparison.

**Next:** source-reliability weighting (§6), calibration + walk-forward (§8 step
3–4), and an interactive local **Math Lab** (sliders over prior/half-life/
risk-aversion that plot the posterior, threshold, P(edge), Kelly, and commitment)
so the brain is a cockpit, not a cave.
