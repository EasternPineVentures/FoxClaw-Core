# Anti-Poisoning Layer V0

Status: EXISTS.
Last updated: 2026-06-27.

## Doctrine

No untrusted input becomes truth directly.

Raw source material must move through:

```text
Raw intake
  -> Quarantine
  -> Scoring / corroboration
  -> Receipt
  -> Public packet
  -> Outcome review
  -> Source reputation update
```

There is no direct path from raw intake to a CoinFox public packet.

## Why V0 Is Lean

V0 exists to catch obvious poisoning before live packet data compounds. It is deliberately
small because FoxClaw does not yet have enough real packet outcomes to justify automated
source reliability scoring or reputation updates.

This pass adds deterministic, standard-library-only checks. It does not add networking,
database writes, model calls, live trading, wallet behavior, or source score mutation.

## Modules

- `foxclaw/security/prompt_injection.py` flags obvious instruction-smuggling phrases.
- `foxclaw/security/quarantine.py` keeps new sources quarantined by default and allows
  public packet influence only when a source is trusted or independently corroborated.
- `foxclaw/security/packet_trust_metadata.py` emits public-safe review labels after the
  same guard decision, without source scores or authority changes.
- `tools/coinfox_packet_demo.py --intake <path>` can quarantine-check raw intake before
  rendering a curated CoinFox packet.

## Trusted Source Caveat

Trusted sources bypass the new-source quarantine rule only.

Trusted sources do not bypass prompt-injection scanning. If a trusted source includes
instruction-smuggling text such as "ignore previous instructions" or "treat this as truth",
the observation stays quarantined.

## Source Registry V0

`config/public_source_registry.json` now supplies `source_state` defaults for known public
sources when intake observations include a `source_id`.

Unknown sources still default to quarantine. Trusted sources bypass new-source quarantine
only, not prompt-injection scanning.

`docs/curated_packet_soak_fixtures_v0.md` records the synthetic fixture matrix that exercises
these rules and `docs/packet_trust_metadata_v0.md` records the V0 label sidecar.

## Deferred To V1

- source reliability scoring;
- source reputation updates from outcomes;
- node receipt signing;
- Ed25519 or other cryptographic verification;
- incident logging;
- database-backed quarantine queues;
- CoinFox UI presentation of trust metadata;
- live source automation.

The right V1 trigger is one to two weeks of real curated packet data.
