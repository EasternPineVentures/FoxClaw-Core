# Packet Trust Metadata V0

Status: EXISTS.
Last updated: 2026-06-27.

## Purpose

Packet Trust Metadata V0 adds a small public-safe label sidecar to the CoinFox curated
packet intake guard.

It answers:

```text
What kind of source/provenance risk did this intake observation carry?
```

It does not answer:

```text
Is this source reliable forever?
Should this become verified memory?
Should this trade be executed?
```

## Demo Command

```powershell
python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_intake\manual_market_pulse_intake.valid.json --trust-metadata
python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_soak\unknown_clean_two_corroborations.allowed.json --json --trust-metadata
```

Without `--trust-metadata`, the packet demo behaves as before.

## V0 Fields

Each evaluated intake observation emits:

- `schema_version`;
- `label`;
- display text;
- public-safe source type;
- source trust state;
- corroboration count;
- prompt-injection flag;
- guard allow/block result;
- decision reason;
- hard false authority locks.

The metadata intentionally does not emit:

- raw source text;
- source IDs;
- source names;
- source URLs;
- private receipt IDs;
- local file paths;
- source scores;
- confidence values;
- reputation updates.

## Labels

| Label | Meaning |
| --- | --- |
| `trusted_provenance` | Known public provenance passed the V0 guard after prompt scanning. |
| `prompt_injection_blocked` | Instruction-like source text was blocked before packet rendering. |
| `unverified_social_heat` | Public social attention is context, not truth. |
| `new_source_corroborated` | A new public source passed only after independent corroboration. |
| `new_source_needs_corroboration` | A new public source remains quarantined until corroborated. |
| `watch_source_corroborated` | A watch source became review material after corroboration. |
| `watch_source_needs_corroboration` | A watch source remains watch-only until corroborated. |
| `private_text_blocked` | A private-text export attempt was blocked before packet rendering. |
| `odds_move_watch` | Prediction-market odds are context, not settled truth. |

## Authority Boundary

Every metadata record has:

```text
can_train_model = false
can_update_verified_memory = false
can_change_source_reliability = false
can_promote_evidence = false
can_authorize_execution = false
can_submit_order = false
can_move_funds = false
live_execution_allowed = false
```

This is review metadata only. It can help CoinFox or an operator explain why a public-safe
packet card is tentative, corroborated, blocked, or watch-only. It cannot promote evidence,
change source reliability, mutate FoxClaw memory, or authorize execution.

## Relation To Soak Fixtures

The soak fixture matrix remains the edge-case harness:

```text
tests/fixtures/coinfox_packet_soak/
```

`tests/security/test_packet_trust_metadata_v0.py` verifies that each soak fixture receives
the expected V0 label and that metadata output does not leak raw observation text or source
identifiers.

## Deferred

- source reliability scoring;
- confidence labels or confidence scores;
- outcome-based reputation updates;
- CoinFox UI presentation;
- database-backed trust metadata storage;
- automatic source ingestion.

The right next trigger is real packet usage and outcome review, not more labels in advance.
