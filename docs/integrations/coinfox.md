# CoinFox Integration

Status: EXISTING PRODUCT BONES; FOXCLAW CONTRACT SCAFFOLD.
Owner repo: EasternPineVentures/CoinFox.
Upstream owner: EasternPineVentures/foxclaw-core.
Resume location: this file.
Tracking issue: EasternPineVentures/CoinFox#TBD.

## Current State

CoinFox remains an early-stage public product with real bones in place, but it
requires substantial internal framework and UX work. FoxClaw Core must not assume
CoinFox services, tables, APIs, engagement pipelines, or presentation components
are complete or polished.

Local read-only check on 2026-06-19 found the reference checkout at
`C:\Users\brend\EPV_Dev\coinfox`. It already has a social store, post/comment/vote
tests, a mobile app with feed/post/account-style surfaces, WebSocket feed pieces,
and community/social code. It is also active WIP, dirty, and behind origin, so do
not treat that snapshot as clean release truth.

CoinFox is not only a FoxClaw intelligence-card renderer. The big product vision
is a social trading surface: a familiar feed where users can post trade ideas,
ask questions, talk about markets, follow long-running theses, comment on
anything, upvote posts and comments, and branch discussions in a fluid social
style.

The bones exist, but the product still needs a ton of work. The current feel is
still too on-rails and clunky for the final goal. We will make it feel like a
real social product people already understand.

The product should feel closer to a native social network people already
understand than to a rigid guided workflow. The reference pattern is a familiar
live feed with fast posting, comments, repost-like spread, nested or branching
conversation, and topic discovery. CoinFox owns that feel.

## FoxClaw Core Provides

- public intelligence schemas;
- Public Contract v1 manifest and compatibility rule;
- versioned example payloads;
- validation rules;
- public-safe identifiers;
- fixture data for CoinFox development;
- deterministic reference exports under `runtime_exports/coinfox/`;
- explicit boundaries for attention, evidence, readiness, and publication.

## CoinFox Must Eventually Build

- post persistence;
- free-form trade-idea and trading-discussion posting;
- general market discussion threads;
- post upvotes and comment upvotes;
- comment persistence;
- branching comment/reply conversations;
- real-time or near-real-time feed updates;
- follow/watch flows for long-running trade ideas;
- idea lifecycle views for trades that take weeks or months to play out;
- spotlighting for useful discussion and strong calls;
- engagement-event collection;
- attention aggregation;
- feed ranking;
- authentication and permissions;
- public intelligence API client;
- intelligence cards and risk displays;
- moderation and reporting;
- outcome and postmortem views.

## Social Product Doctrine

CoinFox must not feel like users are trapped on rails. It should support open
conversation about anything trading-related while still letting FoxClaw
intelligence appear as structured context when it is useful.

Important social primitives:

- user posts;
- comments on every post;
- branching replies;
- post and comment upvotes;
- follows/watchlists for people, topics, and long-running ideas;
- live discussion around active market events;
- visible idea history as a call develops over time;
- spotlight surfaces for useful posts, good calls, and accountable postmortems.

Voting and discussion are product signals. They may influence attention,
discovery, and what deserves review. They must not become evidence truth by
themselves.

## Forbidden Coupling

- no FoxClaw database access;
- no import of `foxclaw.engine`;
- no access to Apollo private data;
- no mutation of Grove receipts;
- no use of CoinFox popularity as evidence truth.

## Contract-First Rule

During the FoxClaw foundation phase:

- CoinFox integration is contract-first.
- Proposed CoinFox paths are marked PLANNED or SCAFFOLD.
- Every dependency includes an owner, status, GitHub issue, and resume trigger.
- FoxClaw Core publishes schemas and fixtures only.
- CoinFox later implements persistence, engagement, ranking, moderation, API
  client, and presentation layers.
- CoinFox consumes only versioned public contracts.
- CoinFox should refuse unsupported public-contract major versions.
- No FoxClaw private implementation is copied into CoinFox.
- CoinFox social content remains user-generated until converted into a structured
  claim through an explicit intake/promotion path.

## Current FoxClaw Export Contract

FoxClaw now has a deterministic reference exporter:

```text
python tools/export_public_intelligence.py --fixture --output runtime_exports/coinfox
```

Expected output:

```text
runtime_exports/coinfox/manifest.json
runtime_exports/coinfox/intelligence_cards.jsonl
runtime_exports/coinfox/scorecard.json
runtime_exports/coinfox/outcomes.jsonl
```

Every exported card states:

```text
contract_version = 1.0.0
author_type = system
author_display = FoxClaw
mode = informational_paper
publication_class = DERIVATIVE_PUBLIC_SAFE or PUBLIC_SOURCE
contains_private_source_content = false
live_execution_allowed = false
not_individualized_advice = true
```

CoinFox should use these files as its first integration target before wiring a
live FoxClaw client.

## Attention Events CoinFox May Aggregate Later

```text
post_impression
post_open
post_dwell
post_save
post_share
post_comment
watchlist_add
forecast_submit
open_in_planifier
paper_plan_created
outcome_page_return
post_reported
```

FoxClaw should receive aggregates, not CoinFox's full private user-event stream.

## Resume Trigger

Resume inside the CoinFox repository after A2's parser inventory is reviewed and
the remaining Discord parser compatibility work is either ported or explicitly
deferred. The first CoinFox pass should preserve the existing social bones, add a
FoxClaw public-contract client, ingest fixture cards, collect sanitized attention
aggregates, and reshape the feed into the open trading-social surface.
