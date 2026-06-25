# CoinFox Week 1 Community Games Design

Status: Approved for manual Week 1 soft-launch test.
Date: 2026-06-25.
Owner: CoinFox founder/operator.
Repository context: `foxclaw-core` documents the public safety boundary; Discord operations happen in the live CoinFox server.

## Context

The CoinFox Discord reset is an in-place conversion of the existing server, not a
second Discord. As of this design, the archive has been verified, the public
CoinFox structure exists, legacy visibility has been reduced, first launch pins
exist, and no public invite is active.

The next community step is not more channel architecture. It is a small manual
Week 1 test that proves whether the CoinFox culture loop works with real people:

```text
idea -> thesis -> invalidation -> confidence -> risk -> resolution -> postmortem -> reputation
```

CoinFox should feel like a trader gym, prediction arena, and build-in-public
clubhouse. It should not feel like a real-money trading contest, paid signal
room, or profit-only leaderboard.

## Goals

- Test whether users enjoy competing on process, evidence, calibration, risk
  control, and postmortems.
- Keep the public Discord simple by running games inside existing public channels.
- Teach the doctrine that a good signal is not automatically a good trade.
- Reward "stay out" reasoning and no-edge calls as valuable contributions.
- Produce public-safe examples that can later become product fixtures, content,
  or structured game mechanics.
- Learn whether the games create useful engagement or noisy channel clutter.

## Non-Goals

- Do not create an `ARENA` category for Week 1.
- Do not create real-money contests, paid games, gambling systems, token rewards,
  or copy-trading mechanics.
- Do not rank users by profit alone.
- Do not present any game result as financial advice, investment advice, verified
  performance, or a guaranteed-profit system.
- Do not automate scoring, roles, or leaderboards before the manual format is
  proven.
- Do not expose Founder Vault, Reset Staging, raw archive, raw signal, parser,
  or bot-log material.

## Chosen Approach

Run Week 1 manually inside existing public channels:

| Game | Channel |
| --- | --- |
| Prediction Duels | `market-talk` |
| Good Signal, Bad Trade Court | `trade-ideas` and `good-signal-bad-trade` |
| No-Edge Challenge | `no-edge-rejects` |
| Postmortems | `foxclaw-postmortems` |
| Weekly game schedule | `announcements` |

This keeps the server readable during the first invite wave. If the games show
activity and the existing channels become crowded, create an `ARENA` category
after the Week 1 review.

## Pre-Week-1 Gates

Before inviting the first soft-launch group:

- New and Member visibility has been tested.
- `FOUNDER VAULT`, `RESET STAGING`, archive exports, hidden legacy channels,
  parser logs, bot logs, and raw signal history are not visible to public roles.
- Old invites remain revoked.
- One soft-launch invite lands in `START HERE`.
- Rules and launch pins are visible.
- Basic safety moderation is configured or manually covered.
- The CoinFox representative bot remains mention-only if enabled.

Discord-native features can support this later. Community Onboarding can route
members into roles/channels by questions; Forum channels can keep ideas from
being buried; Scheduled Events can notify users before game sessions; AutoMod
can block or flag risky spam terms. These are useful primitives, but Week 1 does
not require turning every game into a new Discord feature.

Reference docs:

- Discord Community Onboarding FAQ: https://support.discord.com/hc/en-us/articles/11074987197975-Community-Onboarding-FAQ
- Discord Forum Channels FAQ: https://support.discord.com/hc/en-us/articles/6208479917079-Forum-Channels-FAQ
- Discord Scheduled Events: https://support.discord.com/hc/en-us/articles/4409494125719-Scheduled-Events
- Discord AutoMod FAQ: https://support.discord.com/hc/en-us/articles/4421269296535-AutoMod-FAQ

## Game 1: Prediction Duels

Purpose: make users state probabilistic beliefs with evidence and resolution
criteria.

Placement: `market-talk`.

Prompt template:

```text
Prediction Duel: [market/event/question]

Resolution source:
Resolution time:
Side A:
Side B:

Each side must post:
- thesis
- public evidence
- what would change their mind
- confidence %
- risk label
- invalidation or resolution condition
```

Scoring:

| Item | Points |
| --- | ---: |
| Correct direction or resolved outcome | +3 |
| Public evidence | +2 |
| Clear invalidation or resolution condition | +2 |
| Reasonable confidence calibration | +2 |
| Clean postmortem | +2 |
| Overconfidence penalty | -2 |
| No invalidation | -2 |
| Hype-only thesis | -3 |

The point is not to reward the loudest correct call. It is to reward a forecast
that can be checked later.

## Game 2: Good Signal, Bad Trade Court

Purpose: teach the line between an interesting signal and an executable trade.

Placement: `trade-ideas` for the original idea and `good-signal-bad-trade` for
the review.

Prompt template:

```text
Good Signal, Bad Trade Court

Idea:
Thesis:
Signal evidence:
Entry or watched level:
Invalidation:
Risk label:
Why this could fail:

Verdict options:
- Structured
- Watch Only
- Good Signal, Bad Trade
- Redline
- Reject
```

Review roles:

| Role | Responsibility |
| --- | --- |
| Defender | Explains why the setup is structured. |
| Prosecutor | Explains why the setup could be a bad trade. |
| Judge | Moderator, founder, or trusted scout summarizes the verdict. |
| Jury | Community reacts or comments with reasoning. |

Scoring rewards:

- thesis clarity;
- invalidation quality;
- risk awareness;
- willingness to stay out;
- identifying bad entry, leverage, liquidity, crowding, or unclear resolution;
- clean verdict summary.

## Game 3: No-Edge Challenge

Purpose: make "no trade" feel like a respected win.

Placement: `no-edge-rejects`.

Prompt template:

```text
No-Edge Challenge

Popular idea:
Why it looks tempting:
Possible hidden problem:
Evidence needed:
Why FoxClaw might reject it:
What would make it worth reviewing again:
```

Users earn reputation for spotting:

- weak evidence;
- bad liquidity;
- late entry;
- crowd already priced in;
- ambiguous resolution;
- unsupported hype;
- hidden correlation;
- missing invalidation;
- bad reward-to-risk;
- conditions where the best move is to stay out.

## Postmortems

Purpose: turn resolved ideas into learning.

Placement: `foxclaw-postmortems`.

Prompt template:

```text
Postmortem: [idea/event]

Original thesis:
Original confidence:
Original invalidation:
Outcome:
What was right:
What was wrong:
Was this a good idea even if it lost:
Was this a bad idea even if it won:
What changes next time:
```

Postmortems are eligible for reputation even when the idea was wrong. A clean
review is more valuable than a lucky result with no reasoning.

## Reputation Model

Week 1 reputation is manual and lightweight. The founder/operator can summarize
standouts in `announcements` or `wins-and-lessons`.

Reward:

- clear thesis;
- public evidence;
- defined invalidation;
- calibrated confidence;
- risk awareness;
- willingness to stay out;
- clean postmortem;
- respectful disagreement;
- useful beginner explanation.

Do not reward:

- profit screenshots without context;
- pressure to trade;
- guaranteed-profit claims;
- spammy ticker calls;
- private DM signal solicitation;
- ridicule of losses;
- pretending paper discussion is live financial advice.

## Week 1 Schedule

Use `announcements` for the weekly schedule.

Suggested rhythm:

```text
Monday: Market Map and open prediction prompts
Tuesday: Prediction Duel
Wednesday: Good Signal, Bad Trade Court
Thursday: No-Edge Challenge
Friday: Postmortem Friday
Weekend: Founder summary in wins-and-lessons
```

If the server is quiet, run fewer sessions. A good Week 1 is clean and learnable,
not busy.

## Moderation And Safety

Block or remove:

- guaranteed profit;
- risk free;
- 100% win;
- send wallet;
- private key;
- seed phrase;
- DM me for signals;
- paid signal pressure;
- pump group coordination;
- impersonation;
- stolen or private material.

Every game post should preserve these boundaries:

- paper-only;
- informational;
- public evidence only;
- no personalized financial advice;
- no pressure to enter a trade;
- no real-money contest.

## Week 1 Review

After Week 1, review:

- participation;
- moderation burden;
- channel clutter;
- safety issues;
- whether new members understood the rules;
- whether users posted process or only outcomes;
- whether the games improved conversation quality;
- whether an `ARENA` category is now justified.

Create `ARENA` only if the games show enough activity and existing channels are
too crowded.

Possible future `ARENA` layout:

```text
ARENA
- prediction-duels
- paper-portfolio-league
- good-signal-bad-trade
- no-edge-challenge
- redline-gauntlet
- chart-ctf
```

That future layout is deliberately deferred. Week 1 proves the behavior before
the server adds more rooms.

## Success Criteria

Week 1 succeeds when:

- the soft-launch group can participate without seeing private material;
- at least one game produces a public-safe thesis, invalidation, confidence, and
  postmortem trail;
- no game is framed as financial advice or real-money competition;
- moderation load stays manageable;
- user feedback says the server feels understandable;
- the founder/operator can decide whether games deserve their own `ARENA`
  category.

## Self-Review

- Placeholder scan: no placeholder markers or incomplete channel names remain.
- Scope check: this is manual Week 1 Discord operations only, not product
  automation or a CoinFox app build.
- Boundary check: no live trading, real-money prizes, raw archive publishing, or
  signal-copying system is included.
- Consistency check: existing public channels are used; `ARENA` is explicitly
  deferred until after the Week 1 review.
