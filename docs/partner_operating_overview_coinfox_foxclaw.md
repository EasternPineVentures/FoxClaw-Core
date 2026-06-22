# FoxClaw And CoinFox Operating Overview

Status: partner-facing working draft.
Last updated: 2026-06-22.

This document explains, in plain English, how the Eastern Pine market-intelligence system
works today, how FoxClaw and CoinFox fit together, what the system can learn over time, and
where a serious partner could help.

It intentionally avoids private source details, credentials, proprietary thresholds, and
internal-only implementation specifics.

## Short Version

Eastern Pine is building a receipt-backed market intelligence system.

The core idea is simple:

```text
Markets create a flood of claims, opinions, setups, data, and reactions.
Most platforms let that information disappear into a feed.
We want to turn useful market discussion into structured, auditable intelligence.
```

FoxClaw is the guarded intelligence engine. It keeps the receipts: what was claimed, what
evidence existed, what was missing, how risky the setup was, what happened later, and what
should be learned.

CoinFox is the public-facing market discussion and intelligence product. It gives people a
familiar social surface to post ideas, ask questions, comment, vote, follow theses, and see
plain-English market reads.

The long-term goal is for CoinFox to become a high-quality public intelligence network where
market ideas are not just posted and forgotten. They become trackable, reviewable, and useful
for better AI-assisted decision support.

## The Main Products

### FoxClaw

FoxClaw is the private/guarded decision-intelligence layer.

It is not a social app. It is not a brokerage. It does not need to place trades to be useful.
Its job is to organize messy information into structured decision support.

FoxClaw watches incoming claims and turns them into a receipt chain:

- what came in;
- where it came from;
- whether it parsed cleanly;
- whether it had enough evidence;
- whether it was public-safe;
- whether it was actionable or only worth watching;
- what happened after the fact;
- what the system should learn.

FoxClaw is deliberately paper-first and receipt-first. That means the system can practice,
measure, and learn without pretending it has live execution authority.

### CoinFox

CoinFox is the public market-intelligence and social layer.

It is designed to feel familiar: a feed, posts, comments, votes, share links, market reads,
and public discussion around trade ideas. The current public answer contract is intentionally
simple:

- `LONG`: current evidence leans upward;
- `SHORT`: current evidence leans downward;
- `NEUTRAL`: evidence is mixed, weak, or not directional enough.

CoinFox also has the direction of setup posts, opinion posts, question posts, comments,
Boost/Fade-style voting, shareable links, account gates, and play-money practice through
NYFE. The product should stay open for browsing while requiring verified accounts for
posting, voting, commenting, predictions, and play-money exchange actions.

CoinFox is where the public data flywheel can form. If users post ideas, update theses,
challenge claims, vote, follow, and return after outcomes, the platform can learn from the
entire lifecycle of market conversation.

### Planifier

Planifier is the planning and practice layer.

If FoxClaw says, "Here is the intelligence," and CoinFox says, "Here is the discussion,"
Planifier asks, "What is your plan?"

Planifier should help users turn public intelligence into checklists, journals, routines,
and self-awareness. It should not become FoxClaw's scoring authority or CoinFox's feed
ranking engine.

### Redshift

Redshift is the research and simulation lane.

It is for higher-risk ideas, paper execution rehearsal, market experiments, and protected
research. Redshift can return paper outcomes and context back to the system, but it should
not become the source of public truth or capital authority.

### Apollo / Courier

Apollo and Courier are the node-coordination layer for internal work.

They help A1/A2-style founder nodes know which branch, lane, and work state they are on.
They are not public user infrastructure. They are there to keep development and internal
coordination clean as the system gets larger.

## How Information Moves Through The System

The core flow looks like this:

```text
Discord / CoinFox posts / public data / news / trusted evidence
  -> raw source event
  -> parse attempt
  -> claim packet
  -> evidence bundle or quarantine
  -> readiness and risk review
  -> publication decision
  -> public-safe CoinFox card or private-only preview
  -> paper outcome / resolved outcome
  -> learning receipt
```

In plain English:

1. Something enters the system.
   It might be a Discord signal today, a CoinFox post tomorrow, a public market feed, a news
   event, or a trusted evidence packet.

2. The system records that it saw it.
   This is the first receipt. We do not want important market information floating around
   without a timestamp and origin.

3. The system tries to understand it.
   Is it a trade setup, a question, an opinion, a news claim, a market event, or noise?

4. The system separates evidence from attention.
   A post can be popular without being true. A quiet post can be valuable. CoinFox attention
   can tell FoxClaw where to look, but attention does not become evidence by itself.

5. The system checks risk and readiness.
   A good thesis is not automatically a good trade. A setup may have strong evidence but poor
   timing, bad liquidity, missing invalidation, or too much event risk.

6. The system decides what can be public.
   Private source details, raw Discord content, internal IDs, and private lineage stay
   private. Public outputs must be sanitized and contract-valid.

7. Outcomes are recorded.
   If a paper thesis plays out, resolves, fails, or gets voided, that outcome is attached to
   the original idea.

8. The learning loop updates review memory.
   The system can later ask, "Have we seen this kind of setup before? Did it work? What was
   missing? Did the crowd catch something useful? Did the market baseline do better?"

## Why The Discord Parser Still Matters

The Discord parser is still useful because it gives the system a starting stream of market
claims and setups while CoinFox is still growing.

It is a bridge, not the final center of gravity.

Right now, Discord-style sources can help provide:

- early market ideas;
- parser compatibility examples;
- accepted/rejected examples;
- reason codes;
- paper outcome history;
- training examples for future claim extraction.

Over time, if CoinFox works, the most valuable input should shift toward CoinFox itself:

- user setup posts;
- question threads;
- comments that challenge a thesis;
- Boost/Fade votes;
- saved/followed ideas;
- revisions over time;
- postmortems;
- play-money practice outcomes;
- public evidence added by the community.

The transition is important. We do not want to depend forever on private Discord flow. But we
also do not want to turn off useful data before CoinFox has enough public activity to replace
it.

The practical plan is:

```text
Discord/parser data fills the early pipeline.
CoinFox user activity gradually becomes the public-native data source.
FoxClaw keeps both behind the same receipt and privacy rules.
```

## What CoinFox Data Can Teach

A normal social network learns what gets attention.

CoinFox should learn more than that.

It can learn:

- which users make useful calls over time;
- which setup types work in which market regimes;
- which theses attract hype but fail;
- which quiet ideas later prove valuable;
- which comments identify missing risk;
- which invalidation levels mattered;
- which symbols attract poor-quality crowd behavior;
- which posts led users to make better plans;
- which sources or evidence types improved outcomes;
- which public reads were helpful, confusing, or ignored.

That is valuable because it gives AI a structured memory to reason over. Instead of asking an
AI to summarize a noisy feed, we can ask it to review a chain of receipts:

```text
What was claimed?
What evidence existed?
What did people notice?
What was missing?
What happened?
What should we learn?
```

That is a better AI problem.

## Attention Is Useful, But It Is Not Truth

CoinFox will naturally produce social signals:

- views;
- comments;
- votes;
- saves;
- shares;
- watchlist adds;
- prediction actions;
- return visits after outcomes.

These are important signals. They show where the crowd is looking and where review may be
needed.

But they cannot directly decide whether a claim is true.

The rule is:

```text
Attention can raise review priority.
Evidence must still earn promotion.
Outcome learning must come from resolved results.
```

This protects the platform from becoming a hype machine.

## Public Versus Private

The system is designed with a public/private boundary.

Private FoxClaw may store:

- internal lineage;
- private source references;
- raw parser diagnostics;
- rejected examples;
- evidence hashes;
- model and policy diagnostics;
- private replay data.

CoinFox may show:

- public-safe cards;
- market read summaries;
- evidence and risk categories;
- paper-only labels;
- public outcome summaries;
- sanitized attention aggregates;
- user posts and public discussion;
- plain-English explanations.

CoinFox should not consume FoxClaw internals directly. It should consume public contracts and
exported artifacts. That is how we protect private data and IP while still giving users
something useful.

## What The User Sees

A user should not feel like they are reading an internal machine log.

They should see:

- a clear `LONG`, `SHORT`, or `NEUTRAL` market read;
- why CoinFox leans that way;
- what would weaken the thesis;
- whether sources are healthy;
- what the community is discussing;
- what evidence is strong, weak, or missing;
- whether a setup is research, watch, structured, tactical, speculative, redline, or rejected;
- comments and votes from other users;
- outcome history and postmortems;
- play-money practice context when appropriate.

The product should feel social and alive, but the intelligence layer should stay disciplined.

## What A Partner Should Understand

This is not only a trading app.

It is a market-intelligence memory system with a social front end.

The potential value is not just "people can post trade ideas." The value is that those ideas
can be:

- timestamped;
- discussed;
- challenged;
- followed;
- compared to evidence;
- connected to outcomes;
- reviewed by AI later;
- used to improve future decision support.

That creates a data asset that normal feeds do not have.

## Where A Partner Could Help

A serious partner could help in several ways.

### Product And UX

CoinFox needs to feel like a real social product, not a rigid workflow.

Useful help:

- social feed design;
- post/comment/reply UX;
- mobile and web polish;
- profile and reputation surfaces;
- notification and follow/watch flows;
- onboarding and plain-English education;
- making charts/media/posts feel native.

### Data And Market Coverage

Early CoinFox must provide useful data before its own community is large.

Useful help:

- public market-data partnerships;
- symbol coverage;
- news and event feeds;
- asset-class expansion;
- cleaner source-health monitoring;
- historical outcome datasets;
- replay/evaluation data.

### Community And Moderation

If CoinFox becomes active, moderation and community quality become core infrastructure.

Useful help:

- verified-account flows;
- anti-spam systems;
- report/moderation queues;
- reputation models;
- creator/trader onboarding;
- beta community management;
- safe rules for public claims.

### AI And Evaluation

The system needs AI that can reason over receipts, not just generate commentary.

Useful help:

- retrieval over historical receipts;
- setup clustering;
- postmortem generation;
- claim extraction from user posts;
- evidence-gap detection;
- attention-versus-evidence analysis;
- model evaluation and calibration;
- privacy-preserving learning workflows.

### Security, Compliance, And IP

This system touches market discussion, user-generated content, public claims, and private
intelligence.

Useful help:

- public wording review;
- privacy review;
- IP/trademark review;
- security review;
- contributor agreements;
- data-retention policy;
- terms and moderation policy.

## What We Should Not Do

To keep the project durable, we should avoid:

- presenting CoinFox as financial advice;
- implying live trading authority;
- letting votes become truth;
- exposing private FoxClaw lineage;
- copying private parser data into public fixtures;
- relying forever on Discord instead of building CoinFox-native data;
- over-sharing proprietary scoring internals too early;
- building a beautiful feed with no outcome learning;
- building a powerful engine with no human-friendly social surface.

The product only becomes special if both sides work:

```text
CoinFox makes market conversation accessible.
FoxClaw makes market conversation accountable.
```

## Current Reality

What exists now:

- FoxClaw Core has the receipt-first engine direction, public/private contract boundary,
  Microscope private preview and staged export scaffolding, parser compatibility work, and
  learning-receipt doctrine.
- CoinFox has real product bones: public `LONG` / `SHORT` / `NEUTRAL` reads, FastAPI
  surfaces, social post/comment/vote endpoints, mobile screens, play-money NYFE direction,
  source-health concepts, feedback learning, and public sharing plans.
- The Discord parser remains a useful bridge while CoinFox-native activity is still early.
- Security and IP boundaries are documented and should stay visible before broader launch or
  partnership work.

What still needs work:

- CoinFox needs a polished web/social experience.
- Auth and verified-email contribution gates need production hardening.
- Public CoinFox cards and FoxClaw exports need a professional presentation layer.
- CoinFox attention receipts need to be defined and integrated.
- Parser compatibility needs to finish so early data can be replayed safely.
- Outcome learning needs to expand from deterministic examples into real reviewed histories.
- Moderation, reporting, trust, and partner-safe data access need more structure.

## The Near-Term Plan

This week should be CoinFox-focused.

The practical order:

1. Stabilize the CoinFox public product shape.
   Make the Read, Community, Post, Account, and NYFE surfaces understandable.

2. Define the CoinFox-to-FoxClaw contract.
   Decide exactly what post, vote, comment, attention, and outcome data can become public-safe
   receipts.

3. Keep Discord/parser data as bridge input.
   Do not over-invest in Discord as the future, but preserve useful data until CoinFox has
   enough native activity.

4. Build public-safe intelligence cards.
   Make FoxClaw output readable inside CoinFox without exposing private lineage.

5. Make the social feed feel natural.
   Posting, commenting, voting, following, and revisiting outcomes need to feel like a modern
   social product.

6. Add learning loops.
   The platform should remember whether a thesis worked, failed, changed, or never became
   actionable.

7. Prepare partner-safe demos.
   Show public surfaces, proof markers, and learning logic. Do not show private databases,
   raw Discord content, internal IDs, or protected scoring details.

## The Big Bet

The big bet is that the next generation of market intelligence will not be won only by the
best model or the fastest feed.

It will be won by the system with the best structured memory.

CoinFox can generate the public discussion layer. FoxClaw can turn that discussion into
receipts, evidence, outcomes, and learning. Planifier can help users turn intelligence into
personal discipline. Redshift can test harder ideas in protected simulation.

Together, that becomes more than a dashboard.

It becomes a market-intelligence network that can learn.
