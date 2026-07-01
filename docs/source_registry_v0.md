# Source Registry V0

Status: EXISTS.
Last updated: 2026-06-27.

## Purpose

Source Registry V0 gives FoxClaw a small deterministic map from `source_id` to the default
`source_state` used by Anti-Poisoning V0.

It does not fetch, scrape, score, rank, or verify live source content. It only answers:

```text
When intake says this came from source_id X, what default quarantine policy applies?
```

The starter registry lives at:

```text
config/public_source_registry.json
```

For the broader "where should we look first?" map, use:

```text
docs/source_discovery_inventory_v0.md
config/source_discovery_inventory.json
```

Discovery inventory entries are candidates only. They do not become trusted registry sources
until they pass source policy review.

## Connection To Anti-Poisoning V0

The CoinFox packet demo intake guard now prefers registry policy when an observation has a
`source_id`.

```text
intake observation
  -> source_id lookup
  -> source_state
  -> prompt-injection scan
  -> quarantine decision
  -> curated packet or sanitized block
```

Unknown sources still use `default_source_state(...)` and start quarantined.

## Trusted Source Caveat

Trusted source means trusted provenance, not trusted content.

Official public sources such as `sec_edgar`, `fred`, `bls`, `treasury`, `nasdaq_public`,
and `nyse_public` may bypass new-source quarantine. They still require prompt-injection
scanning before they can influence a public packet.

## Unknown Source Behavior

Unknown sources are quarantined by default.

They cannot influence a public CoinFox packet until the quarantine decision sees enough
public corroboration and a clean prompt-injection scan.

The soak fixture
`tests/fixtures/coinfox_packet_soak/unknown_clean_two_corroborations.allowed.json` proves
that unknown sources are not permanently blocked when they are clean and independently
corroborated.

The broader matrix in `docs/curated_packet_soak_fixtures_v0.md` also exercises trusted
official sources, watch/news sources, social/community sources, odds sources, duplicate hype,
and poisoned/private-text attempts.

Packet Trust Metadata V0 uses the registry-derived `source_state` to emit labels such as
`trusted_provenance`, `new_source_corroborated`, `watch_source_needs_corroboration`, and
`odds_move_watch`. Those labels are review metadata only; they do not promote a source,
change source reliability, or create confidence scores.

## Social Source Behavior

Public social/community sources such as `reddit_public`, `discord_public`, `x_public`, and
`stocktwits_public` are quarantined by default.

Social repetition is not truth. It can become review context only after corroboration and
operator review.

## Why There Is No Scoring Yet

V0 avoids source reliability scoring because FoxClaw needs real packet outcomes before the
scores mean anything. A premature score would look precise while still being guesswork.

Source reliability belongs in a later pass after one to two weeks of curated packet data.

## Why Training And Memory Mutation Are Disabled

Every V0 source has:

```text
can_train_model = false
can_update_verified_memory = false
```

The registry can help an observation reach review. It cannot train a model, update verified
memory, or promote evidence into truth. Outcome review and explicit receipts must come first.
