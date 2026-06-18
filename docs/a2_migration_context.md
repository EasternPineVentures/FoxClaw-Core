# A1 / A2 Migration Context

This is the planning brief for coordinating A1 and A2 on the clean `foxclaw-core` repo.

## Short Version

`foxclaw-core` is the new FoxClaw migration target. A1 and A2 are both VSCode workstations
working from this same git repo. The old A2 FoxClaw repo may still be running useful
paper/runtime surfaces, but it is not the product shape we want to carry forward wholesale.

The assignment for A2 is not "port everything." The assignment is:

1. establish current truth;
2. protect the old running organism while it is still needed;
3. decide what deserves to survive;
4. rebuild or port only through the clean FoxClaw v2 boundaries.

FoxClaw is a decision matrix first. The track record, receipts, evidence discipline, and
operator trust model are the asset. Old code is useful only when it proves it still serves
that asset.

## A1 / A2 Workstation Model

There are two active workstations:

- A1: `C:\Users\brend\dev\foxclaw-core`
- A2: `C:\Users\fox1i\Desktop\FoxClaw-Core-master`

They should be treated as two clones of the same repo, not two separate products.

Coordination rules:

- Pull before starting a new slice.
- Commit each completed slice separately.
- Use `tools\apollo_node_brief.py` to send a current node receipt before handing work to
  the other workstation.
- Push only when the slice is ready for the other workstation to pull.
- Avoid editing the same files on both machines at the same time.
- Before switching machines, run `git status --short --branch` and leave the tree clean or
  explicitly say what remains dirty.
- If one workstation is dirty, the other should not guess; inspect or ask before overlapping
  those files.
- VSCode is fine as the working surface, but git status is the source of truth.

See `docs/apollo_node_coordination.md` for the full node-brief protocol.

## A2 First Message

Paste this to A2 after pulling the latest repo:

```text
You are in the new FoxClaw migration target repo. A1 and A2 are working on the same
foxclaw-core git repo from two VSCode workstations.

Current target repo clones:
- A1 path: C:\Users\brend\dev\foxclaw-core
- A2 path: C:\Users\fox1i\Desktop\FoxClaw-Core-master
- Expected version after pull: 0.4.4 or newer
- Expected recent commit: Add Apollo node coordination briefs

The old A2 FoxClaw repo is still treated as the running legacy/reference system. Do not
delete, rename, move, or rewrite it. Start read-only.

Planning output needed first:
1. Confirm repo truth for the new target: branch, latest commit, VERSION, tests available,
   and whether the tree is clean.
2. Confirm old A2 runtime truth read-only: old repo path, visible running processes,
   scheduled tasks/services if any, env files present without revealing secrets, local DB/log
   locations, and what appears to still be active.
3. Produce a Keep / Cut / Port / Rebuild list:
   - Keep: doctrine, receipts, proven behavior, or user workflows worth preserving.
   - Port: small modules that fit cleanly behind adapters or store boundaries.
   - Rebuild: valuable behavior whose old implementation carries too much baggage.
   - Cut: stale, duplicated, unsafe, secret-bearing, or live-authority code that does not
     belong in the public-ready repo.
4. Produce the next sprint plan from that list, limited to the smallest safe slice.

Default answer to your planning menu is: C first, then B.
That means: make the Keep / Cut / Port list first, then turn it into the exact next sprint
plan. Do not begin with a broad roadmap, and do not start cutover work yet.

Hard rails:
- No live orders.
- No funds movement.
- No account authority work.
- No secret printing.
- No DB files committed.
- No OneDrive as source of truth.
- Old repo is reference-only unless explicitly told otherwise.
- Redshift may be used as protected context/research only, not authority.
- Trusted people can feed FoxClaw context, but cannot set probabilities or execute actions.

Two-workstation rules:
- Pull before starting.
- Commit each finished slice separately.
- Use `python tools\apollo_node_brief.py --node-id A2 --peer-node A1 --json` when handing
  status back.
- Keep the tree clean before handing work between A1 and A2.
- Do not edit the same files on both machines at once.
- If the other clone has uncommitted changes, stop and clarify before overlapping.

Strategic direction:
- FoxClaw is a decision matrix first.
- Forecast Desk and football intelligence are a high-value wedge.
- Public credibility comes from receipts, calibration, losing forecast retention, and clean
  evidence handling, not from carrying old code forward.
```

## Which Planning Option To Choose

If A2 asks:

- `A. Migration roadmap`
- `B. Next sprint plan`
- `C. Keep / cut / port list`
- `D. A2 cutover safety plan`

Choose `C first, then B`.

Reason: the old A2 repo has useful operational knowledge mixed with baggage. A roadmap made
too early will accidentally bless the sprawl. A sprint plan made without inventory will miss
important runtime pieces. A cutover plan is premature until we know what, if anything, must
shadow the old repo.

## Current Clean Repo Baseline

As of this brief:

- `foxclaw-core` version is `0.4.4`.
- The active lane is Forecast Desk / Kalshi-first event-contract intelligence.
- The core engine remains domain-neutral.
- Forecast Desk is read-only and paper-only.
- Trusted Evidence Intake V1 exists for context-only evidence submissions.
- Apollo Node Coordination V1 exists for A1/A2 handoff receipts.
- Forecast DB schema is version `3`.
- Latest local verification: `python -m pytest -q` passed with `192 passed`.

## What A2 Should Not Do Yet

A2 should not:

- start moving modules from the old repo directly into `foxclaw-core`;
- add auth or WebSocket demo work without explicit demo credential boundaries;
- create live execution paths;
- use old DBs as authoritative new repo state;
- solve migration by copying old folders;
- introduce new roadmap docs that duplicate existing `HANDOFF.md`, `docs/architecture.md`,
  or `docs/foxclaw_v2_overhaul_plan.md`.

## A2 Planning Deliverable Format

A2 should return a concise planning artifact with these sections:

```text
1. Active Repos
New target:
Old reference:
Not touched:

2. Verified Current Truth
New target branch/version/commit:
New target tests:
Old runtime surfaces:
Old DB/log/env locations:

3. Keep / Cut / Port / Rebuild
Keep:
Cut:
Port:
Rebuild:

4. Risks
Secret risk:
Runtime break risk:
Data lineage risk:
Public-cleanliness risk:

5. Next Sprint
Goal:
Files/modules likely touched:
Tests/receipts required:
Stop conditions:
```

## Good Next Sprint Candidates

After the A2 inventory, likely candidates are:

- Trusted roster/auth boundary for `forecast_evidence_intake.py`, if multiple trusted people
  will submit evidence.
- Football source intake adapters, starting with public-only official/news/weather/injury
  source receipts.
- A2 shadow-run receipt that compares old runtime outputs to new Forecast Desk receipts
  without letting either system control the other.
- Public-ready contributor and getting-started docs if outside collaborators are imminent.

Pick only one small candidate after the inventory. The goal is momentum without baggage.
