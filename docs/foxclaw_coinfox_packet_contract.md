# FoxClaw To CoinFox Packet Contract

Status: EXISTS as public-contract architecture.
Last updated: 2026-06-27.

## Clean Split

FoxClaw is the memory, receipts, and curation engine.

It watches, stores, compares, summarizes, and learns. It keeps the private/internal evidence
chain, source memory, parser lineage, receipt graph, rejected evidence, and outcome learning.

CoinFox is the public discussion and thesis surface.

It shows safe market ideas, public source links, thesis prompts, comments, challenges,
outcomes, and public-safe proof markers. It must not expose raw FoxClaw internals.

The shared surface is a packet contract, not shared implementation.

## Why This Contract Exists

CoinFox needs useful market context on demand:

```text
What should CoinFox care about right now?
```

FoxClaw should answer with 5-10 curated cards, not a firehose:

- what happened;
- where it came from;
- why it matters;
- what the counterpoint is;
- which public source link should be shown;
- what thesis angle CoinFox should invite;
- what should be reviewed later;
- why this is safe to display.

The first version is manual-first. Automation can fill the same shape later, source by
source.

## Public Contract Artifact

Schema:

```text
foxclaw/contract/public/coinfox_curated_packet.schema.json
```

Fixture:

```text
tests/fixtures/public_contract/coinfox_curated_packet.valid.json
```

Demo command:

```powershell
python tools\coinfox_packet_demo.py --fixture
python tools\coinfox_packet_demo.py --fixture --json
```

Anti-poisoning guarded demo command:

```powershell
python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_intake\manual_market_pulse_intake.valid.json
python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_intake\manual_market_pulse_intake.valid.json --trust-metadata
```

Manual intake guidance:

```text
docs/coinfox_curated_packet_intake.md
```

Manual intake fixture:

```text
tests/fixtures/coinfox_packet_intake/manual_market_pulse_intake.valid.json
```

Packet Trust Metadata V0:

```text
docs/packet_trust_metadata_v0.md
```

The trust metadata sidecar is public-safe review metadata only. It labels provenance and
guard state, but does not expose raw source text, source IDs, source URLs, confidence
scores, reputation updates, memory mutation, or execution authority.

The schema supports three near-term packet types:

| Packet type | User-facing command | Purpose |
| --- | --- | --- |
| `market_pulse_now` | Market Pulse Now | What is moving and why. |
| `idea_board_now` | Idea Board Now | Possible thesis prompts with source links. |
| `what_changed_since_yesterday` | What Changed Since Yesterday | Deltas, not just headlines. |

## Packet Shape

Each packet carries:

- `packet_id`;
- `packet_type`;
- `generated_at`;
- `source_window`;
- `supported_commands`;
- `cards`;
- hard authority locks.

Each card carries:

- `card_id`;
- `card_type`;
- `title`;
- `asset_or_topic`;
- `tags`;
- `source_quality`;
- `source_links`;
- `why_interesting`;
- `public_safe_summary`;
- `counterpoint`;
- `confidence`;
- `suggested_thesis_angle`;
- `suggested_coinfox_prompt`;
- `risk_flags`;
- `card_status`;
- `outcome_memory`;
- public safety flags.

This is enough for CoinFox to display a useful market prompt without receiving private
FoxClaw state.

## Source Memory Layer

FoxClaw should remember sources before it automates them.

Source memory eventually tracks:

- articles;
- odds moves;
- social heat;
- filings;
- charts;
- macro events;
- Discord notes;
- Reddit spikes;
- prediction-market gaps;
- why the item mattered at the time.

Every interesting item should become a small structured record:

```text
what happened
source
timestamp
asset/topic
why interesting
counterpoint
confidence
public-safe summary
outcome review question
```

The public packet exports only the safe summary and public links. Private evidence chains
stay inside FoxClaw.

## End-To-End Loop

```text
Sources
  -> FoxClaw source memory receipts
  -> curated public-safe packet
  -> CoinFox thesis/discussion prompt
  -> comments and challenges
  -> outcome review
  -> FoxClaw learning receipts
```

CoinFox discussion can create attention and challenge receipts. It does not become truth by
itself.

## Public Safety Rules

The packet must not include:

- raw Discord/private-source text;
- private source IDs;
- private receipt IDs;
- local file paths;
- private parser artifacts;
- API keys or tokens;
- proprietary scoring internals;
- live trade instructions;
- order or funds authority.

The packet may include:

- public source links;
- public-safe summaries;
- source quality labels;
- source trust tier;
- tags;
- counterpoints;
- suggested thesis prompts;
- outcome-review questions;
- paper-only/no-advice disclosures.

## Manual-First Build Path

1. Operator manually creates 3-10 packet cards from public sources.
2. Intake observations are recorded in a public-safe manual intake fixture.
3. Anti-Poisoning V0 rejects prompt injection and uncorroborated new sources.
4. Packet validates against `coinfox_curated_packet.schema.json`.
5. CoinFox renders the packet as public prompts or admin-reviewed draft cards.
6. Users discuss and challenge the ideas in CoinFox.
7. Outcome review creates follow-up receipts.
8. FoxClaw learns which sources, prompts, and challenges aged well.

Only after this feels useful should automation expand source by source.

## Source Automation Order

Start with sources that are public, linkable, and low-risk:

1. CoinFox-native posts and market theses.
2. Prediction-market public data.
3. Official filings and macro releases.
4. Public market data.
5. Professional news in link-and-summary mode.
6. Social heat as aggregate-only.
7. Private/community sources only after explicit permission and publication policy review.

## Viability Test

The contract is viable when this is true:

```text
FoxClaw can produce a packet in minutes.
CoinFox can show it without private leakage.
Users can challenge it.
The outcome can be reviewed later.
FoxClaw can learn whether the source, prompt, and counterpoint aged well.
```

That is how the system compounds for years without becoming a messy firehose.
