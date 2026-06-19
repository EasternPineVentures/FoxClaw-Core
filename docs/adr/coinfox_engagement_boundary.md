# ADR: CoinFox Engagement Boundary

Status: Accepted.
Date: 2026-06-19.

## Context

CoinFox will eventually own public posts, comments, engagement events, public
feeds, and public presentation. FoxClaw Core owns claims, evidence quality, edge,
readiness, and public contracts.

## Decision

FoxClaw Core receives sanitized CoinFox attention aggregates only through a
versioned contract. CoinFox must not import FoxClaw engine internals, read FoxClaw
databases, mutate Grove receipts, or treat popularity as truth.

## Consequences

- `foxclaw/contract/public/attention_receipt.schema.json` is a contract scaffold,
  not a CoinFox implementation.
- CoinFox persistence, API client, bot detection, feed ranking, and UI remain in
  the CoinFox repo.
- Cross-repo dependencies must be tracked through GitHub issues and project
  fields, not copied task lists.
