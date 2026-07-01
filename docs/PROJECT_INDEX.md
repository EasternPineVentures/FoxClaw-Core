# FoxClaw Core Project Index

Status: EXISTS as the repo orientation layer.
Last updated: 2026-06-27.

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
9. `docs/anti_poisoning_v0.md`, `docs/source_registry_v0.md`, and
   `docs/packet_trust_metadata_v0.md` for the quarantine-first airlock,
   known-source default policy, and public-safe review labels before public packet
   preparation.
10. `docs/foxclaw_coinfox_packet_contract.md`,
   `docs/coinfox_curated_packet_intake.md`, and
   `docs/curated_packet_soak_fixtures_v0.md` for the shared public-safe packet
   boundary, manual intake path, and edge-case soak fixtures between FoxClaw and
   CoinFox.
11. `docs/partner_operating_overview_coinfox_foxclaw.md` for the plain-English
   partner-facing operating overview.
12. `docs/coinfox_one_page_overview.md`, `docs/coinfox_linkedin_about.md`, and
   `docs/eastern_pine_ventures_landing_page_copy.md` for compressed public copy.
13. `docs/integrations/coinfox.md` before doing any CoinFox-facing work.
14. `docs/source_discovery_inventory_v0.md`, `docs/interaction_potential_v0.md`, and
   `docs/apollo1_standalone_intake.md` when A2 or the legacy Discord parser is unavailable
   and A1 needs to find public sources fast, rank likely user reaction, and prepare packet
   intake.
15. `docs/first_encounter_guide.md`, `docs/foxclaw_gym.md`, and
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
| Anti-Poisoning Layer V0 | EXISTS | `foxclaw/security/`, `docs/anti_poisoning_v0.md`, `tests/fixtures/security/` |
| Source Registry V0 | EXISTS | `config/public_source_registry.json`, `docs/source_registry_v0.md`, `foxclaw/security/source_registry.py` |
| Packet Trust Metadata V0 | EXISTS | `foxclaw/security/packet_trust_metadata.py`, `docs/packet_trust_metadata_v0.md`, `tests/security/test_packet_trust_metadata_v0.py` |
| Curated Packet Soak Fixtures V0 | EXISTS | Full matrix in `docs/curated_packet_soak_fixtures_v0.md`, `tests/fixtures/coinfox_packet_soak/` |
| Partner operating overview | EXISTS | `docs/partner_operating_overview_coinfox_foxclaw.md` |
| Compressed partner/public copy | EXISTS | `docs/coinfox_one_page_overview.md`, `docs/coinfox_linkedin_about.md`, `docs/eastern_pine_ventures_landing_page_copy.md` |
| FoxClaw Gym / demo readiness | EXISTS | `docs/foxclaw_gym.md`, `docs/demo_readiness_2026_06_28.md` |
| FoxClaw command center | EXISTS | `config/foxclaw_commands.json`, `docs/foxclaw_commands.md`, `tools/foxclaw_commands.py` |
| First-encounter guide | EXISTS | `docs/first_encounter_guide.md`, `tools/foxclaw_visitor_guide.py` |
| Public contract airlock | FROZEN v1 | `foxclaw/contract/`, `foxclaw/contract/public/`, `tools/export_public_intelligence.py` |
| FoxClaw-to-CoinFox packet contract | EXISTS | `foxclaw/contract/public/coinfox_curated_packet.schema.json`, `docs/foxclaw_coinfox_packet_contract.md` |
| FoxClaw-to-CoinFox coordination contract | V0 DOCS/DEMO | `foxclaw/contract/public/coinfox_coordination_packet.schema.json`, `docs/contracts/foxclaw_coinfox_coordination_contract_v0.md`, `tools/coinfox_coordination_demo.py` |
| Curated packet intake fixture | EXISTS | `docs/coinfox_curated_packet_intake.md`, `tests/fixtures/coinfox_packet_intake/manual_market_pulse_intake.valid.json` |
| Source Discovery Inventory V0 | EXISTS | `config/source_discovery_inventory.json`, `docs/source_discovery_inventory_v0.md`, `tools/source_discovery_inventory.py` |
| Interaction Potential V0 | EXISTS | `config/interaction_potential_v0.json`, `docs/interaction_potential_v0.md`, `tools/interaction_potential.py` |
| Apollo 1 standalone intake | EXISTS | `config/apollo1_intake_lanes.json`, `docs/apollo1_standalone_intake.md`, `tools/apollo1_intake.py` |
| CoinFox live beta integration | ROUGH LIVE BETA | `https://coinfox.foxclaw.cloud/`, `docs/integrations/coinfox.md` |
| Planifier practice layer integration | EXISTS, NEEDS WORK | `docs/integrations/planifier.md` |
| Public/community node validation layer | DEFERRED | `docs/integrations/foxclaw_node.md`, pin P17 |
| Live execution | BLOCKED | `A4_prohibited`, no live authority grant exists |

## Current Foundation Phase

Allowed now:

- FoxClaw Core architecture and doctrine.
- Public-safe information contracts.
- FoxClaw/CoinFox coordination packets as docs/schema/fixtures/demo only.
- Fixture payloads, schema validation tests, and deterministic CoinFox export files.
- Manual-first FoxClaw-to-CoinFox curated packets.
- Minimum viable anti-poisoning checks before raw intake can influence packet rendering.
- Known public-source default policy for packet intake via Source Registry V0.
- Curated packet soak fixtures for edge-case intake behavior.
- Packet Trust Metadata V0 labels for public-safe provenance/guard review, with no
  confidence scores or source reputation mutation.
- Apollo 1 standalone manual/public intake while A2 and the legacy Discord parser are
  unavailable.
- Source Discovery Inventory V0 for fast public source hunting, with Reddit split out as a
  quarantined social lane.
- Interaction Potential V0 for ranking public-safe observations by likely useful user
  reaction, without turning engagement into truth.
- CoinFox integration notes.
- Live-beta readbacks of the public CoinFox surface, as long as implementation changes stay
  in the CoinFox repo.
- GitHub issue and dependency mapping.

Deferred:

- CoinFox app implementation changes from this repo.
- CoinFox post/comment/vote persistence changes unless working inside the CoinFox repo.
- CoinFox engagement persistence and feed ranking changes unless working inside the CoinFox repo.
- CoinFox mobile UI changes unless working inside the CoinFox repo.
- Contributor-node runtime.
- Personalized recommendation systems.
- Automated source reliability scoring and reputation updates.
- Legacy Discord/parser automation until A2 inventory returns.
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

Resume work through the command center:

```text
python tools\foxclaw_commands.py
```

Use `python tools\foxclaw_commands.py --run gym` when you want the next smallest
rehearsal slice. Do not build CoinFox internals from this repository.
