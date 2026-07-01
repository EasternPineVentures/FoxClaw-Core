# FoxClaw Public Contract

Status: FROZEN v1.
Owner: EasternPineVentures/foxclaw-core.
Boundary: public-safe, read-only, versioned contract artifacts.

This directory is the public airlock. CoinFox, Planifier, and future public
nodes may consume these shapes. They must not import `foxclaw.engine`, read
FoxClaw databases, mutate Grove receipts, or receive Apollo private data.

## Current Contract Files

| File | Status | Purpose |
| --- | --- | --- |
| `manifest.json` | FROZEN | Contract name, version, schema versions, and compatibility rules. |
| `VERSION` | FROZEN | Current public contract version. |
| `public_intelligence_card.schema.json` | FROZEN | Public card describing a claim, evidence, attention, tradeability, risk, and plan readiness. |
| `public_scorecard.schema.json` | FROZEN | Public-safe separated measurements for one intelligence snapshot. |
| `attention_receipt.schema.json` | FROZEN | Sanitized CoinFox attention aggregate. |
| `coinfox_curated_packet.schema.json` | FROZEN | Public-safe FoxClaw-to-CoinFox packet for Market Pulse, Idea Board, and daily-delta cards. |
| `coinfox_coordination_packet.schema.json` | V0 ADDITIVE | State-machine packets for FoxClaw/CoinFox intent, decision, action, and outcome receipts. |
| `risk_classification.schema.json` | FROZEN | Risk taxonomy and presentation requirements. |
| `verified_outcome.schema.json` | FROZEN | Public postmortem/outcome shape. |

## Authority Boundary

Public contracts may describe decision support. They do not grant authority.

```text
author_display = FoxClaw
mode = informational_paper
contains_private_source_content = false
live_execution_allowed = false
not_individualized_advice = true
authority = paper_only or review_priority_only
```

## Compatibility Rule

- Patch: clarification or backwards-compatible validation.
- Minor: additive optional fields.
- Major: breaking field or semantic change.

CoinFox must refuse unsupported major versions rather than silently guessing.

`coinfox_coordination_packet.v0` is a demo/contract artifact only. It does not wire
FoxClaw into CoinFox production behavior, and it does not grant publication, trading,
custody, lending, or advice authority.

## Resume Rule

When adding a new public field:

1. Add it to the schema.
2. Add it to a fixture under `tests/fixtures/public_contract/`.
3. Update `tests/unit/test_public_contract_schemas.py`.
4. Document the owning repository and resume trigger.
