# FoxClaw Gym

Status: EXISTS as first-encounter readiness layer.
Last updated: 2026-06-27.

The gym is where the foxes get clear before people encounter the project. It is
not a live trading surface, not a pitch deck, and not a replacement for tests. It
is a small, repeatable readiness loop that answers:

```text
Where are we heading?
What can we prove today?
What needs attention next?
What would a first-time person understand without a long explanation?
```

## Demo Target

Target first showing: June 28, 2026.

Purpose: let family and curious wedding guests understand the shape of FoxClaw
clearly and safely without needing trading background:

- FoxClaw gathers public information.
- It separates attention from evidence.
- It separates a signal from a trade.
- It stays paper-only.
- It learns from outcomes.
- CoinFox is now a rough live beta at `https://coinfox.foxclaw.cloud/`, with social
  trading, market, prediction, thesis, discussion, FESC, account-gate, and public
  disclaimer surfaces visible enough for controlled real-user testing.
- Planifier is already built, but needs work before it becomes the polished
  practice layer for this flow.

## Gym Rule

A demo item is not ready because it sounds good. It is ready when it has a drill,
a proof command, a short demo line, and a next action.

## Daily Loop

Run:

```powershell
python tools\foxclaw_gym.py
```

For machine-readable output:

```powershell
python tools\foxclaw_gym.py --json
```

Each day, update `config/foxclaw_gym_drills.json` only when the proof has changed:

- `ready`: proof works and the first-encounter line is understandable.
- `practice`: proof exists, but the explanation or visitor surface needs polish.
- `scaffold`: shape exists, but the demo artifact is incomplete.
- `planned`: no useful artifact yet.
- `blocked`: cannot move until a named dependency lands.

## Demo-Critical Drills

| Drill | Current status | Why it matters |
| --- | --- | --- |
| Public Contract Airlock | ready | Shows safe contracts instead of private internals. |
| Forecast Desk Doctor | ready | Shows honest silence and paper-only health. |
| Public Hunt Export | practice | Shows public-safe paper intelligence artifacts. |
| Redshift Paper Boundary | ready | Shows information traveling without authority. |
| Forecast Learning Spine | ready | Shows paper outcomes becoming learning. |
| CoinFox Live Beta And Card | practice | Shows the live beta plus where public-safe intelligence context belongs. |
| Planifier Practice Rehearsal | practice | Shows "the user is the variable" using the existing Planifier product direction. |
| Visitor First Encounter | ready | Makes the whole thing understandable without a pitch. |
| Demo Single-Command Doctor | ready | Keeps us honest about readiness. |

## What Needs Attention First

The gym starts with these attention priorities:

1. Review the public-demo threat model.
2. Keep the CoinFox live beta and public card readable without raw JSON.
3. Create a Planifier plan draft fixture linked to the public intelligence snapshot.
4. Practice the public hunt export and decide what files are shown.

## Hard Boundary

The gym may render visitor guides, export fixtures, and validate contracts. It may
not submit orders, move funds, load production credentials, or imply that a
scaffolded repo is finished.

Before showing the gym outside the build loop, read
`docs/security_public_demo_threat_model.md`.
