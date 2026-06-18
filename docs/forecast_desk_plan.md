# FoxClaw Forecast Desk — Plan (P10, Kalshi-first)

*Started: 2026-06-17 · Status: private founder architecture · grounded against `foxclaw-core` @ v0.2.0*

The Forecast Desk is a new **scope** for FoxClaw's signals, not a new product line: the same
free signals ([[free-signals-strategy]]), now covering **event-contract markets** where the
edge is *mispriced probability*. It reuses the decision spine already built (edge → score →
gate, v0.2.0) through the same adapter border the market scoreboard uses.

> **Three states, said everywhere:** Brain live in **paper**. Money **not** live. Public
> **not** live.

---

## 1. Doctrine — hunt mispriced probability, not high-probability events

```
usable_edge =  FoxClaw_probability
             − market_implied_probability
             − spread
             − fees
             − slippage
             − legal / account restrictions
```

A 95% event priced at 98¢ is not interesting. A 62% event priced at 43¢ may be the edge. The
edge comes from **better reasoning over public evidence**, never from privileged access
(invariant #11). This formula is locked in code in `foxclaw/adapters/event_contracts/pricing.py`
— the doctrine is testable, not just prose.

## 2. What the Forecast Desk does / does not do

It exists to: discover event markets · build evidence dossiers · estimate FoxClaw probability ·
compare against market-implied probability · simulate paper positions · score resolved outcomes
· learn which categories FoxClaw is actually good at.

It does **not**: create accounts · connect wallets · deposit funds · route live orders · bypass
jurisdiction rules · rely on an LLM to approve anything · use nonpublic/insider/hacked/classified/
private information (invariant #11).

## 3. Venue posture — Kalshi first

Kalshi is the cleanest first US lane (a CFTC-designated contract market; public market-data
endpoints are reachable read-only without authentication). FoxClaw's posture there:

- ✅ read-only public market data · ✅ paper simulation · ✅ dossier building
- ❌ no deposits/accounts/wallets · ❌ no live order routing · ❌ no VPN/offshore workarounds ·
  ❌ no LLM approval path

Describe the broader space as **emerging, partially regulated, jurisdiction-sensitive** — never
"unregulated." The space is actively moving (CFTC rulemaking + state-level disputes ongoing), so
the doctrine is: **Kalshi first because it is the cleanest regulated path; every other venue
requires a separate, founder-approved, venue-and-jurisdiction-specific review** before any work
beyond reading public data. This document is architecture, not legal advice.

## 4. Hard locks (enforced in code, see invariant #1 + #11)

Every `foxclaw/adapters/event_contracts/*` module sets `can_submit_order=false`,
`can_move_funds=false`, live eligibility **always false**, default authority `A4_prohibited`. No
`live_trade` / `submit_order` / `buy` / `sell` / `execute` / `fund_move` action is permitted.
Going live is a separate, reviewed, founder-approved authority pass — never a default.

## 5. Build sequence

| Phase | Module / tool | Deliverable |
|---|---|---|
| 0 (now) | `event_contracts/pricing.py` | **Doctrine in code:** price ↔ implied probability, edge gap, usable edge. Pure, tested. |
| 1 | `venues.py`, `eligibility.py`, `markets.py` | Kalshi metadata; jurisdiction/account gate (always false for live); read-only market catalog normalization. |
| 2 | `dossiers.py`, `pricing.py`, `resolution.py` | Evidence + resolution-source packets; pricing; settlement evidence. |
| 3 | `paper.py`, `tools/event_contract_scanner.py`, `tools/event_contract_paper_simulator.py` | Paper-only event receipts; rank markets by edge gap; simulate entry/exit. |
| 4 | `store/` `event_outcomes`, `tools/forecast_scoreboard.py`, Founder Cockpit | Receipt storage; win-rate / profit-factor / edge-accuracy scoreboard; read-only visibility. |

Sequence after each step: `pytest` stays green; the invariant guard stays green (all market/venue
vocabulary stays in the adapter, `engine/` stays domain-neutral).

## 6. Capitalization (the business lens — held throughout)

Free signals are **distribution**: attention/adoption is the scarce resource, not the signal.
We capitalize on the layers *around* the free signals, roughly by how soon / how clean:

1. **Sell / license the system** — the Forecast Desk + decision engine as a product. Cleanest
   path: no fund custody, no live-trading legal exposure, investor-legible. The
   professionalization plan (`docs/professionalization_plan.md`) is what makes this saleable
   (clean repo, proof report, one-command demo).
2. **Node-access tiers / CoinFox** (pin **P11**) — access to a personal fox + deeper intelligence
   is *earned by contribution*, never a paywall and never profit-share/token-yield/custody. The
   separate commercial layer, architecturally outside the engine.
3. **Operate it ourselves for P&L** — only by going **live**, which is a separate founder-approved
   compliance + authority grant (invariant #1). Real money is a deliberate later gate; until then
   everything is paper-first and the track record is being earned, not spent.

Design rule: never let capitalization compromise the free-signal surface or the paper-only/
read-only posture. The product is the *engine and the proof*, not gating the signals.

## 7. Current state it builds on (grounded, do not overclaim)

- `foxclaw-core` @ **v0.2.0**: store spine + paper execution + engine (edge, trust, gate, score,
  one tier owner) + the **market scoreboard chain** (`assess_setup`: outcomes → observations →
  edge → score-tier → gate-multiplier → receipt-compatible verdict). Suite **100 green**,
  invariant guard passing.
- The scoreboard gate is a **live paper gate** on A2 (`shadow=false`, `source_overrides`
  neutralized to 1.0) — live in paper, not money, not public.
- The Forecast Desk reuses this spine; it is the **producer/venue** side feeding the same engine.

---

See `docs/deferred.md` (P10, P11), `docs/invariants.md` (#1 paper-only, #4 domain-neutral, #11
public-information-only), and `docs/professionalization_plan.md` (the saleability path).
