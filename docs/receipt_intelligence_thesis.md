# Receipt Intelligence Thesis

Status: working doctrine.
Audience: Eastern Pine Ventures, FoxClaw, CoinFox, Planifier, and future node work.

## Core Claim

Receipts are the difference between a system that remembers and a system that merely reacts.

FoxClaw should not only say what it thinks. It should preserve how an idea entered the
system, what evidence supported it, what was missing, how people reacted, what decision was
made, what happened later, and what should be learned from that outcome.

That record is the asset.

## Why Receipts Beat Untracked Discussion

Without receipts, market discussion becomes short-lived noise:

- people remember winners and forget losers;
- strong claims lose their timestamp and context;
- popularity gets mistaken for truth;
- AI summaries become detached from the original evidence;
- no one can replay what was known at decision time;
- the same mistakes repeat because there is no durable learning trail.

With receipts, the system can keep a structured memory:

- the original claim;
- the timestamp;
- the source class;
- the evidence available at the time;
- what was unknown;
- the attention around the claim;
- the readiness and risk state;
- the paper decision or stand-down;
- the resolved outcome;
- the learning signal after the fact.

That turns trading conversation into a replayable intelligence graph instead of a feed that
forgets itself every few hours.

## What A Receipt Is

A receipt is a durable record of a transformation.

Examples:

- raw source event received;
- parse attempt accepted or rejected;
- claim packet created;
- evidence bundle promoted or quarantined;
- attention aggregate observed;
- readiness verdict issued;
- paper position rehearsed;
- outcome resolved;
- learning signal generated;
- public card exported.

The receipt does not need to expose private content publicly. Internal receipts can retain
private lineage for audit, while public receipts can expose only the safe proof markers:
contract version, timestamp, status, evidence quality, risk class, paper-only label, and
outcome summary.

## Why This Matters For AI

AI gets much more useful when it can learn from structured history instead of raw chat.

A receipt ledger gives AI:

- examples of claims that looked good but failed;
- examples of boring claims that were actually useful;
- source and setup track records over time;
- calibration data against market baselines;
- before-and-after snapshots for outcome review;
- evidence-quality patterns;
- hype and crowd-heat patterns;
- rejected examples with explicit reasons;
- duplicate and coordinated-push patterns;
- decision timing and missed-confirmation patterns.

This lets AI do better work:

- retrieve the closest historical analogs;
- challenge weak assumptions;
- spot missing invalidation logic;
- flag when attention is rising faster than evidence;
- separate "good thesis" from "good trade right now";
- identify which sources or setup types deserve review;
- generate cleaner postmortems;
- recommend what evidence should be gathered next.

The goal is not AI that guesses harder. The goal is AI that can reason over a record of what
was believed, why it was believed, and what reality later proved.

## Why CoinFox Is Valuable

CoinFox can become more than a trading social feed because it can preserve the lifecycle of
ideas.

A normal social feed can show:

- what is trending;
- who posted first;
- who got attention;
- who sounded confident.

CoinFox plus receipts can show:

- when the thesis was first stated;
- how it changed;
- what evidence was added;
- what people challenged;
- whether the idea had a plan;
- whether it was paper-rehearsed;
- whether it resolved;
- whether the original reasoning held up.

That is a different product. It creates accountability without turning the platform into a
copy-trading casino.

## The Attention Boundary

Attention is useful, but attention is not evidence.

CoinFox activity can produce attention receipts:

- views;
- saves;
- comments;
- upvotes;
- watchlist adds;
- disagreement;
- returns after outcome;
- open-in-Planifier events.

Those receipts can tell FoxClaw where to look next. They cannot prove a claim is true, alter
source reliability by themselves, authorize a trade, or increase capital allocation.

The correct use of attention is review priority:

```text
crowd heat -> reassess evidence -> maybe promote, maybe quarantine, maybe reject
```

The wrong use is:

```text
many votes -> must be true
```

## Public Presentation Near Term

The public surface should not show the whole private machine.

Near-term public presentation should show three layers:

1. Human-readable idea state.
   What is the claim, what is the evidence, what is missing, and what would change the view?

2. Proof markers.
   Contract version, paper-only label, evidence quality, readiness state, risk class,
   timestamps, and public-safe outcome state.

3. Learning record.
   Did the idea resolve? Did FoxClaw beat the market baseline? Was the paper result good,
   flat, losing, or void? What should be reviewed next?

Public cards should be calm and professional. They should not expose raw Discord content,
private source IDs, receipt IDs, evidence hashes, private candidate lineage, or anything that
looks like a live trade instruction.

## What We Need To Prove

The thesis is not proven by saying "AI plus trading data is valuable." It is proven by
showing that receipts create better review and learning.

Minimum proof ladder:

1. Coverage.
   Can the system consistently turn claims into structured receipt chains?

2. Safety.
   Can private lineage stay private while public-safe cards remain useful?

3. Calibration.
   Do forecast probabilities and evidence-quality labels improve against resolved outcomes?

4. Market baseline comparison.
   Does FoxClaw sometimes beat the market-implied baseline on Brier score or decision quality?

5. Rejection value.
   Do rejected or stand-down receipts prevent bad trades instead of disappearing as "no
   action"?

6. Attention value.
   Do CoinFox attention receipts help prioritize useful review without becoming fake truth?

7. Learning value.
   Do postmortems change future review behavior, source weighting, or setup assessment in a
   measurable way?

## High-Value Metrics

The first useful scoreboard should track:

- claims observed;
- claims parsed;
- claims rejected, with reason codes;
- evidence bundles promoted;
- items quarantined;
- public cards exported;
- paper decisions made;
- stand-down decisions made;
- resolved outcomes;
- Brier score vs market baseline;
- paper result by setup type;
- attention-to-evidence mismatch count;
- public-safe leakage test result;
- duplicate/conflict suppression count;
- learning receipts generated.

This creates an honest company story:

```text
We are not claiming every call is right.
We are proving the system remembers what happened and gets harder to fool over time.
```

## Strategic Direction

The market is moving toward AI agents that can read, summarize, route, and act on data. The
scarce thing will not be "more AI output." The scarce thing will be trustworthy, structured,
permissioned history that agents can safely learn from.

FoxClaw's receipt system positions Eastern Pine Ventures around that scarce asset:

- structured claim memory;
- evidence and attention separation;
- outcome-linked learning;
- public/private contract boundaries;
- paper-only safety;
- social discussion that can become analyzable without becoming reckless.

That is how we get in front of the market: not by making louder predictions, but by building
the cleanest memory of how ideas become decisions and how decisions become lessons.

## Near-Term Build Focus

1. Keep Microscope private previews and staged public exports strict.
2. Finish parser compatibility so claims can enter through a replayable path.
3. Use `coinfox_curated_packet.v1` as the manual-first Market Pulse / Idea Board packet.
4. Add CoinFox attention receipts as sanitized aggregates.
5. Build public cards that show proof markers without private lineage.
6. Connect resolved outcomes to learning receipts.
7. Use Planifier to turn public intelligence into user-owned plans and journals.
8. Score the system weekly with receipt metrics, not vibes.

The first public promise should be modest:

```text
Eastern Pine builds receipt-backed market intelligence: claims, evidence, risk, attention,
paper outcomes, and learning records kept separate enough to be audited and connected enough
to teach better AI review.
```
