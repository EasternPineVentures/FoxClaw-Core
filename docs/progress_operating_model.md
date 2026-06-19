# FoxClaw Progress Operating Model

Progress is not how busy the nodes feel. Progress is a chain of receipts that proves the
system became cleaner, safer, more useful, or more predictive without losing the old track
record.

## Progress Lanes

FoxClaw tracks progress in five lanes.

1. Build progress

   Evidence:

   - committed slices;
   - version bumps;
   - green tests;
   - invariant checks;
   - clean handoffs.

2. Migration progress

   Evidence:

   - old A2 repo read-only inventory;
   - Keep / Cut / Port / Rebuild decisions;
   - fewer unknown runtime surfaces;
   - no wholesale folder copying;
   - no secrets or DBs moved into git.

3. Decision-quality progress

   Evidence:

   - forecast receipts;
   - public evidence dossiers;
   - calibration reports;
   - Brier score and market-baseline comparison;
   - losing forecasts preserved and reviewed.

4. Paper-continuity progress

   Evidence:

   - old paper runtime remains observable while needed;
   - new paper receipts can shadow old outputs;
   - paper fills include costs, slippage, depth, and settlement;
   - no live authority added.

5. Node-coordination progress

   Evidence:

   - Apollo node briefs before handoff;
   - clean A1/A2 trees or explicit dirty-file lists;
   - no overlapping edits;
   - exact next request for the peer node.

## Weekly Scoreboard

At least once per operating cycle, answer these questions:

- What commit advanced the product?
- What test or receipt proves it?
- What old-repo uncertainty was reduced?
- What decision-quality metric changed?
- What paper process is still old and why?
- What is the next smallest safe slice?

If a week has activity but cannot answer those questions, the work may be motion rather than
progress.

## Current Progress Definition

The current build is making progress if it does all of the following:

- keeps `python -m pytest -q` green;
- keeps `python tools\check_invariants.py` green;
- keeps the worktree clean at handoff;
- keeps Forecast Desk read-only and paper-only;
- keeps Redshift context or paper-execution work outside FoxClaw authority;
- shrinks the old A2 repo unknowns through Keep / Cut / Port / Rebuild decisions;
- improves football/event-contract intelligence through public evidence and receipts.

## Stop Conditions

Stop and write a decision note before continuing if:

- a change requires live order, account, wallet, or funds authority;
- a node needs to read or print secrets;
- old paper trading logic is about to be copied wholesale;
- Redshift is about to become an authority source instead of a paper/context lane;
- the old A2 runtime must be modified to keep moving;
- A1 and A2 have dirty overlapping files.

## Current Progress Slice

The current high-signal slice is `FoxClaw Gym / June 28 demo readiness`:

1. Keep the family-demo target visible.
2. Track demo-critical drills with proof commands.
3. Keep a daily next-attention list.
4. Add threat-model checks before any outside-facing demo.
5. Preserve paper-only and public-contract boundaries.

Implemented proof:

```powershell
python tools\foxclaw_gym.py --fixture
python -m pytest tests\unit\test_foxclaw_gym.py -q
```

This slice turns "where are we heading?" into a repo-owned readiness report instead of a
chat-only plan.

## Next Progress Slice

The next high-signal slice is to reduce the gym's `not_ready` demo-critical count:

- rehearse `docs/demo_script_2026_06_28.md`;
- review `docs/security_public_demo_threat_model.md`;
- practice `tools/public_intelligence_card_demo.py --fixture`;
- create a Planifier plan-draft fixture linked to the public intelligence snapshot;
- decide which public Hunt export files are shown during the demo.
