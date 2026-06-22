# FoxClaw Core Project Index

Status: EXISTS as the repo orientation layer.
Last updated: 2026-06-22.

This file is the starting point for future ChatGPT, Codex, Copilot, and human
handoffs. Use it when the whole system is too large to keep in one chat window.

## Load-Bearing Rule

GitHub is the coordination layer. Each repository owns one system. Contracts cross
repository boundaries; implementation details do not.

## Read Order

1. `HANDOFF.md` for the current operational state and latest verification receipts.
2. `docs/invariants.md` for rules that no contributor may break.
3. `docs/decisions.md` for decisions already made.
4. `docs/deferred.md` for named pins and deliberate deferrals.
5. `docs/project_boundaries.md` for repo ownership and cross-repo limits.
6. `docs/trading_intelligence_fabric.md` for the new multi-stage framework.
7. `docs/receipt_intelligence_thesis.md` for the receipt-backed intelligence
   thesis and proof ladder.
8. `docs/security_ip_readiness.md` for the security/IP posture before public or
   partner-facing work.
9. `docs/partner_operating_overview_coinfox_foxclaw.md` for the plain-English
   partner-facing operating overview.
10. `docs/integrations/coinfox.md` before doing any CoinFox-facing work.
11. `docs/first_encounter_guide.md`, `docs/foxclaw_gym.md`, and
   `docs/security_public_demo_threat_model.md` before demo/showing work.

## Status Markers

| Marker | Meaning |
| --- | --- |
| EXISTS | Implemented and tested. |
| SCAFFOLD | Path or interface exists, runtime incomplete. |
| PLANNED | Design only. |
| DEFERRED | Deliberately postponed with a trigger. |
| BLOCKED | Cannot proceed until a named dependency lands. |

Every deferred item should carry owner, status, dependency, boundary, resume
location, and a GitHub issue or explicit issue placeholder.

## What Already Exists

| Area | Status | Current source of truth |
| --- | --- | --- |
| Domain-neutral engine spine | EXISTS | `foxclaw/engine/`, `docs/architecture.md` |
| Grove-style local store | EXISTS | `foxclaw/store/`, `docs/db_schema.md` |
| Policy veto layer | EXISTS | `foxclaw/policy/`, `docs/invariants.md` |
| Forecast Desk / Kalshi public-data lane | EXISTS | `foxclaw/adapters/event_contracts/`, `docs/forecast_desk_plan.md` |
| Trusted Evidence Intake V1 | EXISTS | `docs/trusted_evidence_intake.md` |
| Redshift paper boundary | EXISTS | `docs/foxclaw_redshift_paper_boundary.md` |
| Apollo founder node coordination | EXISTS | `docs/apollo_node_coordination.md`, `docs/apollo_mesh_v0.md` |
| Founder node security | EXISTS | `docs/founder_node_security.md` |
| Forecast Learning Spine V1 | EXISTS | `docs/forecast_learning_spine.md` |
| Receipt intelligence thesis | EXISTS | `docs/receipt_intelligence_thesis.md` |
| Security and IP readiness | EXISTS | `docs/security_ip_readiness.md` |
| Partner operating overview | EXISTS | `docs/partner_operating_overview_coinfox_foxclaw.md` |
| FoxClaw Gym / demo readiness | EXISTS | `docs/foxclaw_gym.md`, `docs/demo_readiness_2026_06_28.md` |
| First-encounter guide | EXISTS | `docs/first_encounter_guide.md`, `tools/foxclaw_visitor_guide.py` |
| Public contract airlock | FROZEN v1 | `foxclaw/contract/`, `foxclaw/contract/public/`, `tools/export_public_intelligence.py` |
| CoinFox social/product integration | EXISTING BONES, NEEDS WORK | `docs/integrations/coinfox.md` |
| Planifier practice layer integration | EXISTS, NEEDS WORK | `docs/integrations/planifier.md` |
| Public/community node validation layer | DEFERRED | `docs/integrations/foxclaw_node.md`, pin P17 |
| Live execution | BLOCKED | `A4_prohibited`, no live authority grant exists |

## Current Foundation Phase

Allowed now:

- FoxClaw Core architecture and doctrine.
- Public-safe information contracts.
- Fixture payloads, schema validation tests, and deterministic CoinFox export files.
- CoinFox integration notes.
- GitHub issue and dependency mapping.

Deferred:

- CoinFox post persistence.
- CoinFox engagement persistence and feed ranking.
- CoinFox mobile UI.
- Contributor-node runtime.
- Personalized recommendation systems.
- Any live execution or capital authority.

## Context Block Template

Use this block near intentionally unfinished integration seams. Do not leave naked
comments such as "finish CoinFox later."

```python
# CONTEXT[EPV-COINFOX-INTELLIGENCE]:
# Status: PUBLIC CONTRACT v1 FROZEN
# Owner repo: EasternPineVentures/CoinFox
# Upstream owner: EasternPineVentures/foxclaw-core
# Purpose: Public-safe FoxClaw intelligence payload consumed by CoinFox.
# Exists now: Schema, fixture payloads, validation tests, deterministic reference export.
# Missing in CoinFox: persistence, API client, engagement pipeline, feed ranking, UI.
# Boundary: CoinFox must not import foxclaw-core internals.
# Resume from: docs/integrations/coinfox.md
# Tracking issue: EasternPineVentures/CoinFox#TBD
```

## Next Resume Point

Resume demo-readiness work through the gym:

```text
python tools\foxclaw_gym.py
```

The top `next_attention` item is the next smallest rehearsal slice. Do not build
CoinFox internals from this repository.
