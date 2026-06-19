# Trading Intelligence Fabric

Status: IN PROGRESS doctrine and contract foundation.
Last updated: 2026-06-19.

FoxClaw does not distribute trades. It transforms information into
professionally structured decisions.

The product principle:

```text
A good signal is not automatically a good trade.
```

FoxClaw should help users avoid turning good information into bad trades.

## Governing Rules

Information may travel. Authority may not.

Attention may prioritize investigation. Attention may never become truth by
itself.

Raw information is quarantined. Only promoted, lineage-backed evidence may enter
decision processing.

## The Five Planes

| Plane | Status | Purpose | Authority |
| --- | --- | --- | --- |
| Collection | SCAFFOLD | Gather attributed source events without judging them | observe only |
| Attention | SCAFFOLD | Measure what users are noticing and saving | review priority only |
| Evidence | EXISTS/SCAFFOLD | Turn claims into evidence bundles and promotion receipts | evidence promotion only after checks |
| Decision | EXISTS/SCAFFOLD | Score edge, readiness, risk, and gate verdicts | paper-only decision support |
| Behavior and Education | PLANNED | Help users build plans and practice discipline | user-owned planning only |

Existing Forecast Desk and trusted-evidence work already prove parts of the
Evidence and Decision planes. CoinFox attention and public cards are contract
scaffolds until their owning repo implements them.

## Internal Contract Chain

The internal contract path is separate from the public contract. Internal
objects may include private source references, diagnostics, provider metadata,
quarantine state, and full lineage. CoinFox must never consume internal objects
and remove fields itself.

Current internal v1 foundation:

```text
RawSourceEvent
  -> ParseAttempt
  -> ClaimPacket
  -> EvidenceBundle
  -> AttentionAggregate
  -> TradeabilitySnapshot
  -> TradeReadinessVerdict
  -> PublicationDecision
  -> PublicIntelligenceCard
  -> VerifiedOutcome
```

Parser behavior remains A2-dependent. The contracts are ready now so the legacy
Discord parser can later be ported behind replay-compatible boundaries instead
of copied into a new monolith.

## CoinFox Social Layer

CoinFox is the intended public social layer, not just a place where FoxClaw
publishes cards. The CoinFox repo already has bones for this, but the full social
product feel needs major work. Traders should be able to post trade ideas, ask
general trading questions, comment on anything, upvote posts and comments,
branch discussions, and follow ideas as they unfold over minutes, days, weeks,
or months.

The social feel matters. CoinFox should use familiar social-feed patterns people
already understand: fast posting, live discussion, fluid branching replies,
topic discovery, voting, and spotlighting for useful calls or postmortems. This
open discussion layer belongs in the CoinFox repository.

FoxClaw may consume CoinFox social activity as attributed source events or
sanitized attention aggregates. User posts, votes, comments, and live discussion
do not become truth unless they pass through claim extraction, evidence checks,
quarantine, and promotion.

## Separate Measurements

Do not collapse an idea into one magic score.

| Measurement | Meaning |
| --- | --- |
| Attention | How much interest the subject is receiving. |
| Evidence Quality | Strength, freshness, independence, and traceability. |
| Signal Confidence | Probability the directional or scenario claim is correct. |
| Edge | Difference between FoxClaw estimate and market pricing. |
| Tradeability | Liquidity, spread, slippage, timing, and entry quality. |
| Risk | Volatility, leverage exposure, event risk, gap risk, and loss severity. |
| Plan Readiness | Whether entry, invalidation, target, size, and exit logic exist. |
| Source Track Record | How similar prior claims from the source performed. |
| Setup Track Record | How this setup type historically performed. |
| User Readiness | Whether the user has completed personal plan and risk checks. |

Example verdict:

```text
Signal confidence: 84
Evidence quality: 79
Tradeability: 32
Entry quality: 21
Risk: VERY HIGH
Plan readiness: 0

VERDICT: GOOD THESIS, BAD TRADE RIGHT NOW
```

## Attention Boundary

Attention can:

- raise review priority;
- create a trending flag;
- trigger a fresh evidence scan;
- trigger price/reaction comparison;
- ask FoxClaw to reassess an existing dossier.

Attention cannot:

- approve a candidate;
- promote evidence;
- change source reliability directly;
- authorize a trade;
- increase capital allocation.

When attention rises faster than evidence quality:

```text
label = CROWD_HEAT
verification_status = UNCONFIRMED
decision_authority = NONE
```

## Risk Taxonomy

| Classification | Meaning |
| --- | --- |
| Research | Interesting claim, not yet actionable. |
| Watch | Evidence exists, but entry or confirmation is missing. |
| Structured | Clear thesis, invalidation, liquidity, and acceptable risk. |
| Tactical | Time-sensitive and requires active monitoring. |
| Speculative | High uncertainty or wide outcome distribution. |
| Redline | Extreme volatility, leverage, thin liquidity, or binary risk. |
| Reject | No usable edge, bad terms, or unacceptable ambiguity. |

Redline opportunities must require full-loss acknowledgment, invalidation,
liquidity warning, leverage warning, maximum holding condition, event-risk
disclosure, and paper rehearsal. They must not be beginner-safe or one-click
copy-trade surfaces.

## Information Passport

Every portable information item should carry:

```json
{
  "information_id": "info_example",
  "information_type": "claim",
  "origin": {
    "system": "discord",
    "source_id": "source_public_hash",
    "content_hash": "sha256:example"
  },
  "subject": {
    "asset_or_event": "BTC/USD",
    "direction_or_outcome": "up"
  },
  "timestamps": {
    "observed_at": "2026-06-19T13:15:00Z",
    "expires_at": "2026-06-20T13:15:00Z"
  },
  "scores": {
    "attention": 0.74,
    "evidence_quality": 0.61,
    "source_reliability": 0.52,
    "tradeability": 0.33,
    "risk": 0.86
  },
  "status": {
    "validation": "quarantined",
    "publication": "internal_only",
    "authority": "observe_only"
  },
  "lineage": {
    "raw_event_id": "raw_example",
    "claim_id": "claim_example",
    "evidence_bundle_id": null
  }
}
```

Without the passport, information does not travel.

## Full Flow

```text
Discord / CoinFox / News / Kalshi / Mobile Node
  -> Raw Source Event
  -> Parse Attempt
  -> Claim Packet
  -> Attention Aggregate + Evidence Bundle
  -> quarantine
  -> validate/promote
  -> Tradeability Snapshot
  -> Trade Readiness Verdict
  -> Publication Decision
  -> CoinFox Public Card + Planifier Plan
  -> Paper Outcome
  -> Source / Setup Learning
```

## Anti-Poisoning Invariants

1. Raw content never enters the decision engine.
2. Attention never changes truth or source reliability directly.
3. AI output cannot promote itself.
4. User popularity is not evidence.
5. Every transformation creates a new receipt.
6. Edits create new versions instead of rewriting history.
7. Private-source content cannot become public without a publication path.
8. Duplicate or coordinated activity earns no attention credit.
9. Outcome learning uses verified outcomes, not community sentiment.
10. No single node, post, source, or model can promote evidence alone.
11. A signal cannot be called a trade until readiness requirements pass.
12. A high-risk play must never be presented as beginner-safe.

## Build Sequence

| Phase | Status | Work |
| --- | --- | --- |
| 0 | IN PROGRESS | Doctrine, boundaries, internal/public schemas, sanitized fixtures, validation tests. |
| 1 | PLANNED | CoinFox attention receipts as sanitized aggregates. |
| 2 | PLANNED | Unified claim packets for Discord signals and CoinFox posts. |
| 3 | PLANNED | Quarantine, duplicate filtering, source checks, promotion receipts. |
| 4 | PLANNED | Trade-readiness layer. |
| 5 | PLANNED | CoinFox professional cards. |
| 6 | PLANNED | Planifier connection. |
| 7 | PLANNED | Outcome feedback. |
| 8 | DEFERRED | Node validation after contracts and quarantine are stable. |

Phase 0 is the only active scope in this pass.
