# People Scale And Receipt Viability Plan

Status: EXISTS as planning doctrine.
Last updated: 2026-06-27.

CoinFox is now in rough live beta. That changes FoxClaw's job.

FoxClaw cannot stay only a clever local decision engine. It has to become the protected
receipt backbone that can support many people, many claims, many discussions, many mistakes,
and many resolved outcomes without losing trust.

The goal is not to look big. The goal is to become durable enough that more users create
better structured memory instead of more noise.

## Load-Bearing Thesis

If many people use CoinFox, FoxClaw's receipt system is the company asset.

Receipts must prove:

- what was claimed;
- who or what submitted it, using privacy-safe identifiers;
- when it entered the system;
- what evidence existed at the time;
- what was missing or disputed;
- what attention it received;
- whether it became a structured claim;
- whether it was promoted, quarantined, rejected, or published;
- whether it became a paper decision or stand-down;
- what happened later;
- what the system learned from the outcome.

Without that chain, CoinFox becomes another feed. With that chain, CoinFox becomes a market
memory network.

## Scale Targets

| Stage | People | FoxClaw posture | What must be true |
| --- | --- | --- | --- |
| Private beta | 5-25 trusted users | Manual review, strict fixtures, public routes watched daily | No private leakage, beta users understand paper-only limits, every public card has a contract version |
| Controlled beta | 25-100 users | Moderation queue, attention receipts, issue-backed bugs | Posts/comments/votes cannot become truth, abuse reports are reviewable, deploy health is visible |
| Early public beta | 100-1,000 users | Durable receipt ingest, rate limits, trust tiers, daily scorecards | User activity creates structured receipts, duplicate/coordinated behavior is tracked, exports remain safe |
| Community network | 1,000+ users | Public-node contracts, reputation receipts, replayable audits | Contributors can help validate without receiving private context or authority |

Do not skip stages because the site is live. A live page is not the same thing as a durable
network.

## Minimum Viable Receipt System

Before widening real-user access, FoxClaw and CoinFox need a minimum receipt spine that is
boring, reliable, and replayable.

Required beta receipts:

| Receipt | Owner repo | Purpose | Public-safe output |
| --- | --- | --- | --- |
| `PublicUserActionReceipt` | CoinFox | Records post, comment, vote, follow, report, or save events | Aggregated counts only |
| `AttentionReceipt` | CoinFox -> FoxClaw public contract | Turns activity into review priority | Sanitized attention aggregate |
| `ClaimPromotionReceipt` | FoxClaw | Shows why a user/social item became a structured claim | Status and reason codes |
| `EvidenceReviewReceipt` | FoxClaw | Records accepted, missing, opposing, duplicate, or rejected evidence | Evidence category and quality marker |
| `PublicationDecisionReceipt` | FoxClaw | Decides whether a card can be public | Public/private decision and rejection reason |
| `PublicIntelligenceCard` | FoxClaw public contract -> CoinFox | Displays public-safe context | Claim, risk, readiness, paper-only labels |
| `CoinFoxCuratedPacket` | FoxClaw public contract -> CoinFox | Feeds Market Pulse, Idea Board, and daily-delta prompts | Public links, source quality, thesis angle, counterpoint |
| `VerifiedOutcomeReceipt` | FoxClaw/CoinFox boundary | Records what happened later | Outcome summary and resolution status |
| `LearningReceipt` | FoxClaw | Turns outcomes into calibration and review signals | Public-safe learning summary |

The first scale milestone is not "AI predicts better." It is:

```text
Can a real user post an idea, can the system preserve its lifecycle, and can we review what
happened later without exposing private data or pretending popularity is truth?
```

## People-Scale Operating Lanes

### Product And Onboarding

CoinFox needs a staged beta program:

- invite rings instead of open floodgates;
- a visible beta label and paper-only disclaimer;
- first-session prompts that teach "thesis, evidence, invalidation, risk";
- a clear report flow;
- visible posting/commenting expectations;
- a short explanation of what FoxClaw receipts mean and do not mean.

### Moderation And Trust

Moderation is product infrastructure, not an afterthought.

Minimum controls:

- verified-account gates for posting and voting where needed;
- report receipts with reason codes;
- temporary shadow limits for new accounts;
- duplicate/spam detection receipts;
- manual review queue for high-attention or high-risk posts;
- risk labels before virality labels;
- no public score that rewards hype without outcome review.

### Receipt Data Operations

The receipt ledger needs operational rules:

- append-only by default;
- edits create new versions;
- every receipt has schema version, created timestamp, source system, and authority flags;
- idempotency keys prevent duplicate writes;
- content hashes support deduplication without exposing raw private text publicly;
- public IDs differ from private receipt IDs;
- every public export has a manifest and leakage check;
- backups and restore drills exist before user trust depends on the data.

### Observability

The team needs to know whether the system is healthy before users tell us it is broken.

Minimum beta health surfaces:

- deploy health for CoinFox public app;
- API/data-source health where applicable;
- receipt-ingest counts by type;
- public-export validation result;
- leakage-scan result;
- moderation queue count;
- report count and unresolved age;
- attention-to-evidence mismatch count;
- resolved outcome count;
- learning receipt count;
- top failure reasons.

### Legal, Compliance, And Public Trust

The public language must stay boring and clear:

- no individualized financial advice;
- no live execution;
- no custody;
- no paid signals as the launch promise;
- no guaranteed performance;
- paper-first learning and public discussion only;
- votes are attention, not truth;
- FoxClaw context is decision support, not approval.

## Viability Scoreboard

FoxClaw should measure viability by proof, not vibes.

Weekly metrics:

- active beta users;
- posts created;
- comments created;
- votes/reactions created;
- reports submitted and resolved;
- attention receipts generated;
- claims promoted from public discussion;
- claims rejected or quarantined with reason codes;
- public cards exported;
- public cards blocked by leakage or policy checks;
- resolved outcomes;
- learning receipts generated;
- attention-to-evidence mismatch count;
- top three confusion points from users;
- top three moderation reasons;
- deploy incidents and time to recovery.

The company story becomes stronger when the system can say:

```text
Here is what people claimed, what got attention, what passed evidence review, what was
rejected, what happened later, and what the system learned.
```

## Architecture Direction

### Keep FoxClaw Private And Contract-First

CoinFox may consume public contracts and exported artifacts. It must not import FoxClaw
engine internals, read FoxClaw databases, or receive Apollo private data.

### Make Receipts Portable, Not Private Data Portable

Public systems should receive:

- public-safe card IDs;
- contract versions;
- status markers;
- risk/readiness labels;
- sanitized aggregate counts;
- outcome summaries.

They should not receive:

- private source IDs;
- raw Discord/private text;
- private receipt IDs;
- evidence hashes that reveal private lineage;
- model prompts or private scoring details;
- Apollo founder-private context.

### Prepare For Queues Before They Are Painful

The live beta can start simple, but the architecture should assume asynchronous receipt work:

```text
CoinFox user action
  -> CoinFox event/receipt
  -> sanitized aggregate or candidate claim
  -> FoxClaw intake/review queue
  -> public contract export
  -> CoinFox display
  -> outcome/review loop
```

Do not make synchronous user actions depend on private FoxClaw review. Let users post and
discuss; let FoxClaw receipts upgrade only the parts that deserve structured memory.

## Near-Term Plan

### Phase 1: Beta Control Plane

Owner: CoinFox, supported by FoxClaw contracts.

- Add or confirm deploy health/status checks.
- Define beta invite rings and tester expectations.
- Confirm report/moderation flow.
- Confirm paper-only and no-advice language on public routes.
- Confirm backups for user/social data.

### Phase 2: Receipt Spine V0

Owner: FoxClaw contract design plus CoinFox event capture.

- Freeze `AttentionReceipt` usage for CoinFox beta.
- Define `PublicUserActionReceipt` in the CoinFox repo.
- Add sample public action and attention fixtures.
- Add a daily receipt-count export.
- Prove duplicate and report reason codes are preserved.

### Phase 3: Promotion And Publication

Owner: FoxClaw.

- Convert selected public posts/theses into claim candidates.
- Quarantine by default.
- Require evidence review before promotion.
- Publish only public-safe cards.
- Preserve rejection receipts because avoided bad calls are part of the value.

### Phase 4: Outcome And Learning Loop

Owner: FoxClaw with CoinFox display support.

- Attach outcomes to selected public theses.
- Generate learning receipts.
- Show public-safe postmortems.
- Track whether attention helped review or only created noise.

### Phase 5: Community Node Readiness

Owner: later public-node contract.

- Let contributors perform scoped validation tasks.
- Return signed contribution receipts.
- Never grant trade authority, private context, or source-trust mutation.

## Stop Lines

Do not widen access if any of these are untrue:

- no working rollback path for the public app;
- no way to remove or hide abusive content;
- no report flow;
- no beta-safe disclaimer;
- no backup/restore plan for user content;
- no leakage test for public FoxClaw exports;
- no clear distinction between attention and evidence;
- no owner for moderation decisions;
- no receipt schema versioning;
- no place to record outcome and learning receipts.

## Next Smallest Slice

The next highest-leverage FoxClaw slice is:

```text
Define and test the CoinFox beta receipt spine:
PublicUserActionReceipt -> AttentionReceipt -> CoinFoxCuratedPacket -> ClaimPromotionReceipt ->
PublicationDecisionReceipt -> PublicIntelligenceCard -> VerifiedOutcomeReceipt ->
LearningReceipt
```

The next highest-leverage CoinFox slice is:

```text
Make the live beta operationally testable:
health/status, invite rings, report flow, moderation queue, and beta-safe public wording.
```

Together, these make the system viable: people can use it, the company can learn from it,
and the receipt system becomes stronger as activity increases.
