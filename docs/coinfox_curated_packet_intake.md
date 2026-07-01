# CoinFox Curated Packet Intake

Status: EXISTS as manual-intake guidance.
Last updated: 2026-06-27.

This document describes the manual intake path that turns public market observations into a
FoxClaw-to-CoinFox curated packet.

The intake fixture is not the public export. It is the review worksheet before public export.
CoinFox should consume only the validated curated packet shape:

```text
foxclaw/contract/public/coinfox_curated_packet.schema.json
```

## Fixture

Manual intake fixture:

```text
tests/fixtures/coinfox_packet_intake/manual_market_pulse_intake.valid.json
```

Expected public packet fixture:

```text
tests/fixtures/public_contract/coinfox_curated_packet.valid.json
```

Render the resulting public packet:

```powershell
python tools\coinfox_packet_demo.py --fixture
```

Apollo 1 standalone continuity:

```powershell
python tools\apollo1_intake.py
python tools\source_discovery_inventory.py --limit 20
python tools\interaction_potential.py --intake tests\fixtures\coinfox_packet_intake\manual_market_pulse_intake.valid.json
python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_intake\manual_market_pulse_intake.valid.json --trust-metadata
```

Use this path while Apollo 2 or the legacy Discord parser is unavailable. It keeps CoinFox
market observations moving through public-safe manual intake without connecting Discord or
adding source automation.

## Intake Purpose

The intake step answers:

```text
Should this public observation become a CoinFox prompt?
```

It does not answer:

```text
Is this true?
Should someone trade it?
Should source reliability change?
```

Intake is review priority only. It prepares public-safe context for discussion.

Interaction Potential V0 can rank which included observations are most likely to produce
useful CoinFox comments, challenges, saves, or outcome-review returns. It is ranking only,
not truth or evidence quality.

## Clean Flow

```text
Public observation
  -> intake worksheet
  -> operator review
  -> curated packet card
  -> CoinFox thesis/discussion prompt
  -> comments and challenges
  -> outcome review
  -> FoxClaw learning receipt
```

## Intake Record

Each intake observation should capture:

- `observation_id`;
- `target_card_id`;
- source name and public link;
- source type;
- source trust tier;
- source terms/display status;
- published timestamp;
- asset or topic;
- what happened;
- why it is interesting;
- public-safe summary;
- source state;
- independent corroborations;
- counterpoint;
- confidence;
- suggested thesis angle;
- suggested CoinFox prompt;
- risk flags;
- outcome review question;
- safety flags.

The `target_card_id` maps the intake observation to the card that appears in the public
curated packet fixture.

With Anti-Poisoning V0 enabled, an observation should either come from a trusted source
state or include at least two public corroborations before it is allowed to influence packet
rendering. Trusted sources still pass through prompt-injection scanning.

See `docs/curated_packet_soak_fixtures_v0.md` for edge-case fixtures, including the clean
unknown-source case that passes only after two independent corroborations.

## Intake Safety Rules

The fixture may include only public-safe source metadata and summaries.

Do not include:

- raw Discord/private-source text;
- private channel, guild, user, or message IDs;
- private source names;
- private receipt IDs;
- evidence hashes;
- local file paths;
- API keys, tokens, cookies, or webhook URLs;
- copied article bodies;
- copied social comments;
- live trade instructions.

Use public links and summaries. When terms are unclear, use `blocked_until_review` and do not
include the observation in the public packet.

## Curation Decision

Each included observation should have:

```text
include_in_packet = true
packet_card_type = market_pulse | idea_prompt | delta
card_status = watching | heating_up | confirmed | disputed | fading | post_mortem_ready
reason_codes = [...]
```

Good reason codes:

- `public_link_available`;
- `source_terms_reviewed`;
- `social_heat_only`;
- `needs_primary_source`;
- `prediction_market_move`;
- `daily_delta`;
- `counterpoint_present`;
- `outcome_review_ready`.

## Manual First

This intake path stays manual until the review loop is useful.

Source automation should start only after:

- operators can create useful packet cards manually;
- CoinFox can display the packet safely;
- users understand the prompt and challenge flow;
- outcome review can return later and judge what aged well;
- leakage and authority tests stay green.

The first automation target should be sources with clear public links and simple display
terms. Social heat should remain aggregate-only until its source terms are reviewed.

When CoinFox public posts go live, treat them as public observations only after they have a
public link, public-safe summary, counterpoint, and outcome review question. Comments,
votes, and post velocity are attention signals; they are not evidence truth.
