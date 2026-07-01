# Apollo 1 Standalone Intake

Status: EXISTS.
Last updated: 2026-06-29.

## Purpose

Apollo 2 and the legacy Discord/parser runtime may be unavailable for a few days. FoxClaw
still needs to accept market information, prepare public-safe CoinFox context, and preserve
the evidence boundary from Apollo 1.

This runbook defines what A1 can run now without A2:

```text
manual public observations
  -> Source Discovery Inventory V0
  -> Interaction Potential V0
  -> Source Registry V0
  -> Anti-Poisoning V0
  -> Packet Trust Metadata V0
  -> curated CoinFox packet review
```

This is the continuity path. It is not a Discord scraper, not source automation, not a
CoinFox publisher, and not a live execution path.

## Status Command

```powershell
python tools\apollo1_intake.py
python tools\apollo1_intake.py --json
```

Expected current status:

```text
readiness_status = a1_continuity_ready
required ready = 5 / 5
blocked lanes = 0
deferred to A2 = 2
```

The lane manifest lives at:

```text
config/apollo1_intake_lanes.json
```

## A1-Ready Lanes

### Source Discovery Inventory

Find the fastest public-source lanes before writing packet intake:

```powershell
python tools\source_discovery_inventory.py --limit 20
```

This reports CoinFox-native, Reddit, social, official, news, prediction-market, crypto,
on-chain, and alternative-data discovery sources. It is a source map, not permission to
scrape or publish.

### Interaction Potential

Rank observations by likely useful user reaction before deciding which prompts to draft:

```powershell
python tools\interaction_potential.py --fixture
```

This score predicts comments, challenges, saves, and outcome-review returns. It is not
truth, confidence, evidence quality, or publishing authority.

### Manual Public Packet Intake

Use public links and summaries only:

```powershell
python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_intake\manual_market_pulse_intake.valid.json --trust-metadata
```

This proves that A1 can prepare a curated packet review with trust metadata and authority
locks.

### Source Registry Guard

```powershell
python -m pytest tests\security\test_source_registry_v0.py -q -p no:cacheprovider
```

Known public sources get deterministic default policy. Unknown and social sources remain
quarantined unless independently corroborated.

### Packet Soak And Trust Metadata

```powershell
python -m pytest tests\security\test_curated_packet_soak_fixtures_v0.py tests\security\test_packet_trust_metadata_v0.py -q -p no:cacheprovider
```

This verifies trusted official sources, unknown sources, social heat, watch/news sources,
odds moves, prompt injection, and private-text export attempts.

## A1 Practice Lanes

### Trusted Evidence Intake

This is context-only and Forecast Desk oriented:

```powershell
python tools\forecast_evidence_intake.py --fixture --db data\a1_intake_demo\forecast_desk.db --json
```

Use it only when the local DB target is explicit. Trusted people can submit context; they
cannot set probabilities, promote evidence, publish, or authorize execution.

### Microscope Private Preview

Microscope can remain private review tooling on A1 when a reviewed local DB is available:

```powershell
python tools\microscope.py --help
```

Do not run public staging writes until the parser inventory and publication-promotion gate
are reviewed.

### CoinFox Public Post Bridge

CoinFox is working toward live posts and email verification in its own repo. Until a public
post contract exists, A1 should manually summarize public CoinFox posts into the curated
packet intake worksheet.

CoinFox likes, comments, votes, and post velocity are attention only. They do not become
truth or source reliability.

## Deferred To A2

### Legacy Discord Parser

Do not connect Discord from FoxClaw Core while A2 is unavailable.

Do not copy the old parser into Core as a shortcut. The useful behavior should later be
inventoried and either cut, rebuilt, or ported behind clean replay-compatible boundaries.

### Live Source Automation

Do not add scraping or source automation in this fallback pass.

Manual packets are enough for continuity while CoinFox live posting comes online. Add source
automation one source at a time only after the trust, terms, privacy, and outcome-review
boundaries are explicit.

## Operator Loop For The Next Few Days

1. Watch CoinFox public posts, markets, theses, discussions, and prediction context.
2. Run `python tools\source_discovery_inventory.py --limit 20`.
3. Pick only public-safe observations with a link and a counterpoint.
4. Add or edit a manual intake worksheet.
5. Run `python tools\interaction_potential.py --intake <worksheet>`.
6. Run the packet demo with `--trust-metadata`.
7. Keep unknown/social items quarantined unless there are two independent corroborations.
8. Convert useful observations into public-safe packet cards.
9. Later, review outcomes and update FoxClaw learning receipts.

## Hard Rails

```text
can_submit_order = false
can_move_funds = false
live_execution_allowed = false
can_publish_to_coinfox = false
can_change_source_reliability = false
can_update_verified_memory = false
```

If a lane requires private Discord text, credentials, raw message IDs, hidden parser state,
or source automation, it is not part of Apollo 1 standalone intake.
