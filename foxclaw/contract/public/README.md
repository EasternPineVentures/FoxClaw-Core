# FoxClaw Public Contract

Status: SCAFFOLD.
Owner: EasternPineVentures/foxclaw-core.
Boundary: public-safe, read-only, versioned contract artifacts.

This directory is the public airlock. CoinFox, Planifier, and future public
nodes may consume these shapes. They must not import `foxclaw.engine`, read
FoxClaw databases, mutate Grove receipts, or receive Apollo private data.

## Current Contract Files

| File | Status | Purpose |
| --- | --- | --- |
| `public_intelligence_card.schema.json` | SCAFFOLD | Public card describing a claim, evidence, attention, tradeability, risk, and plan readiness. |
| `public_scorecard.schema.json` | SCAFFOLD | Public-safe separated measurements for one intelligence snapshot. |
| `attention_receipt.schema.json` | SCAFFOLD | Sanitized CoinFox attention aggregate. |
| `risk_classification.schema.json` | SCAFFOLD | Risk taxonomy and presentation requirements. |

## Authority Boundary

Public contracts may describe decision support. They do not grant authority.

```text
can_submit_order = false
can_move_funds = false
live_execution_allowed = false
authority = observe_only or review_priority_only
```

## Resume Rule

When adding a new public field:

1. Add it to the schema.
2. Add it to a fixture under `tests/fixtures/public_contract/`.
3. Update `tests/unit/test_public_contract_schemas.py`.
4. Document the owning repository and resume trigger.
