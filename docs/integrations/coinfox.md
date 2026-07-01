# CoinFox Integration

Status: ROUGH LIVE BETA; FOXCLAW CONTRACT + MICROSCOPE STAGING SCAFFOLD.
Owner repo: EasternPineVentures/CoinFox.
Upstream owner: EasternPineVentures/foxclaw-core.
Resume location: this file.
Tracking issue: EasternPineVentures/CoinFox#TBD.

## Current State

CoinFox is now in rough live beta at:

```text
https://coinfox.foxclaw.cloud/
```

It is close to invite-only real-user testing, but it is not production launch.
FoxClaw Core must still not assume CoinFox services, tables, APIs, engagement pipelines,
or presentation components are complete, stable, or polished.

Live readback on 2026-06-27:

```text
/              -> 200
/markets       -> 200
/predictions   -> 200
/thesis        -> 200
/discussions   -> 200
/fesc          -> 200
/health        -> 404
/api/health    -> 404
/openapi.json  -> 404
```

The visible public surface includes Home, Markets, Predictions, Market Theses,
Discussions, FESC Standards, account gates, public disclaimers, seeded social content,
prediction-market context, and FoxClaw receipt language.

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

The product is now alive enough to test with real people in a controlled beta. It still
needs live-user polish around onboarding, posting/commenting/voting, moderation, empty
states, health checks, account gates, and the public-safe FoxClaw context path before it
should be described as generally launched.

The product should feel closer to a native social network people already
understand than to a rigid guided workflow. The reference pattern is a familiar
live feed with fast posting, comments, repost-like spread, nested or branching
conversation, and topic discovery. CoinFox owns that feel.

## FoxClaw Core Provides

- public intelligence schemas;
- Public Contract v1 manifest and compatibility rule;
- `coinfox_curated_packet.v1` for Market Pulse, Idea Board, and daily-delta cards;
- versioned example payloads;
- validation rules;
- public-safe identifiers;
- fixture data for CoinFox development;
- deterministic reference exports under `runtime_exports/coinfox/`;
- private Microscope previews for accepted-candidate review;
- dry-run-first local staging scaffolds for future public cards;
- explicit boundaries for attention, evidence, readiness, and publication.

## CoinFox Owns In Beta

- production readiness of post persistence;
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
- sanitized attention aggregation;
- feed ranking;
- authentication and permissions;
- public intelligence API client;
- intelligence cards and risk displays;
- moderation and reporting;
- outcome and postmortem views;
- deployment health/status endpoints for beta operations.

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

CoinFox should use these files as the safe integration target before wiring any live
FoxClaw client. The live beta can be tested without giving CoinFox private FoxClaw DB,
engine, or Apollo access.

## Curated Packet Contract

The next shared boundary is the curated packet:

```text
foxclaw/contract/public/coinfox_curated_packet.schema.json
```

It is the safe shape for three CoinFox-facing questions:

```text
Market Pulse Now
Idea Board Now
What Changed Since Yesterday
```

The fixture-backed review command is:

```powershell
python tools\coinfox_packet_demo.py --fixture
python tools\coinfox_packet_demo.py --fixture --json
python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_intake\manual_market_pulse_intake.valid.json --trust-metadata
```

This packet can carry public source links, source quality, public-safe summaries,
counterpoints, suggested thesis angles, risk flags, and outcome-review prompts. It cannot
carry raw FoxClaw internals, private receipt IDs, private source text, or live authority.

Packet Trust Metadata V0 can add a sanitized sidecar for provenance/guard labels such as
`trusted_provenance`, `new_source_corroborated`, `unverified_social_heat`, and
`odds_move_watch`. CoinFox UI presentation is still owned by the CoinFox repo, and these
labels are not source scores or confidence labels.

When A2 or the legacy Discord parser is unavailable, use the Apollo 1 standalone continuity
surface:

```powershell
python tools\apollo1_intake.py
```

This routes FoxClaw through manual public-source packet intake, Source Registry V0,
Anti-Poisoning V0, and Packet Trust Metadata V0. It does not connect Discord, scrape
sources, publish to CoinFox, or consume CoinFox internals.

Resume architecture from `docs/foxclaw_coinfox_packet_contract.md`.

## Microscope V0 Bridge

Microscope V0 is now integrated in FoxClaw Core as a private assessment and safe
staging bridge. It is not a CoinFox API client, not a webhook, and not a live
publisher.

Private operator selection:

```text
python tools/microscope.py --list-recent --limit 10 --db "$env:FOXCLAW_DB"
```

Private proof preview:

```text
python tools/microscope.py --candidate-id <accepted_candidate_id> --db "$env:FOXCLAW_DB" --private-preview
```

The preview must visibly say:

```text
PRIVATE PREVIEW
NOT PUBLISHED
PAPER-ONLY
PUBLICATION CLASS
CONTRACT VERSION
```

The preview must not expose raw Discord text, source IDs, candidate lineage,
receipt IDs, evidence hashes, Discord links, or invented probabilities.

Future local staging, after explicit approval only:

```text
python tools/microscope_batch.py --dry-run --db "$env:FOXCLAW_DB"
python tools/microscope_batch.py --write-staging --db "$env:FOXCLAW_DB" --run-id <reviewed_run_id>
```

The write path is local-only and produces:

```text
runtime_exports/coinfox/staging/<run_id>/manifest.json
runtime_exports/coinfox/staging/<run_id>/cards.jsonl
runtime_exports/coinfox/staging/<run_id>/failures.jsonl
```

Only publication-approved public cards can reach `cards.jsonl`. Each card must
validate against `public_intelligence_card.schema.json` and the semantic
publication/privacy checks. Exact duplicate public IDs are suppressed; conflicting
duplicate IDs produce zero cards for that ID and a sanitized retriable failure.

Do not run a live `--write-staging` batch until A2's legacy Discord parser
inventory and the publication-promotion gate are reviewed.

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

Resume inside the CoinFox repository for beta-readiness work. Preserve the live beta,
verify deploy health, test unauthenticated and authenticated flows, keep public disclaimers
visible, and add FoxClaw public-contract consumption only through `foxclaw/contract/public`
or deterministic exported artifacts. Do not copy FoxClaw internals into CoinFox.
