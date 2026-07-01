# June 28, 2026 Demo Readiness

Status: FIRST-ENCOUNTER READINESS with executable gym checks.
Last updated: 2026-06-27.

June 28, 2026 is the first family/wedding showing target. This is not a public
production launch and not a pitch. It should be clear enough that someone can
understand the shape without a long trading explanation.

## Demo Thesis

FoxClaw helps people avoid turning good information into bad trades.

## System Order

The demo order is:

```text
FoxClaw -> CoinFox -> Planifier
```

FoxClaw is the judgment and receipt engine. CoinFox is now a rough live beta at
`https://coinfox.foxclaw.cloud/`: visible routes include Home, Markets, Predictions,
Market Theses, Discussions, and FESC Standards. It is close to invite-only real-user
testing, but it still needs beta hardening before it should be treated as general public
launch. Planifier is already built as a planning product, but it needs focused work before
it becomes the polished practice layer for this flow.

## First Encounter Path

1. Start with `docs/first_encounter_guide.md` or `python tools\foxclaw_visitor_guide.py`.
2. Move to FoxClaw: the gym, the safety rails, and the public contract airlock.
3. Show FoxClaw's paper-only intelligence proofs: doctor, public export, Redshift
   boundary, and learning spine.
4. Move to CoinFox: show the live beta first, then explain where FoxClaw public-safe
   intelligence cards can appear as context with claim, evidence, attention, risk,
   tradeability, invalidation, trust metadata, and what a professional would wait for.
5. Move to Planifier: explain that it exists, needs work, and is where a user turns
   the intelligence into a personal plan.
6. Close with what is next, not with a promise of live trading.

## Must Be True Before Demo

- `python -m pytest -q` is green.
- `python tools\check_invariants.py` is green.
- `python tools\foxclaw_gym.py --json` shows no demo-critical blocked drills.
- The live CoinFox beta loads the public routes being shown.
- `python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_soak\unknown_clean_two_corroborations.allowed.json --trust-metadata`
  renders public-safe packet output with `new_source_corroborated` and no raw source text.
- `docs/security_public_demo_threat_model.md` has been read before the dry run.
- Every shown artifact is fixture, public-safe, paper-only, or clearly labeled
  scaffold.
- The words "public launch" are framed as direction, not as June 28 production
  readiness.

## June 19-28 Practice Plan

| Date | Focus |
| --- | --- |
| 2026-06-19 | Land the gym and demo-readiness loop. |
| 2026-06-20 | Verify contracts, invariants, and proof commands. |
| 2026-06-21 | Make the first-encounter guide self-explanatory and decide what not to show. |
| 2026-06-22 | Create the CoinFox public card demo artifact. |
| 2026-06-23 | Practice public Hunt export and Redshift boundary. |
| 2026-06-24 | Review the existing Planifier app and create a plan draft fixture. |
| 2026-06-25 | Rehearse learning spine and outcome explanation. |
| 2026-06-26 | Full dry run with no coding during the demo. |
| 2026-06-27 | Fix only blockers and wording confusion. |
| 2026-06-28 | Demo day: show the story, not the whole machine room. |

## What To Avoid

- Do not demo live execution.
- Do not show secrets, local DBs, or private Apollo material.
- Do not imply CoinFox beta status means production launch.
- Do not open too many raw JSON receipts for a non-technical audience.
- Do not chase one more feature if the first-encounter guide is already clear.
