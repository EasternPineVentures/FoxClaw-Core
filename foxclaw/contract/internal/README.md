# FoxClaw Internal Intelligence Contract

Status: v1 foundation, private by default.

These schemas define the private path that produces a public intelligence card.
They may carry source references, diagnostics, quarantine state, provider
metadata, and lineage IDs. CoinFox must not consume these objects directly.

Flow:

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

Rules:

- internal objects are not public exports;
- default publication posture is `INTERNAL_ONLY`;
- every transformation preserves lineage;
- parser replay fixtures must be sanitized before commit;
- private parser fixtures belong under ignored private fixture folders;
- no parser publishes directly to CoinFox.
