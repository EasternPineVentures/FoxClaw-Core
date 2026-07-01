# Curated Packet Soak Fixtures V0

Status: EXISTS.
Last updated: 2026-06-27.

## Purpose

Curated Packet Soak Fixtures V0 catches edge cases in the FoxClaw-to-CoinFox intake guard
before source automation exists.

These fixtures prove whether an intake observation is allowed or quarantined by the current
Anti-Poisoning V0 and Source Registry V0 rules. Packet Trust Metadata V0 now uses this same
matrix to verify public-safe review labels, without adding confidence scores or source
reputation mutation.

## Matrix

| Fixture file | Source type | Expected result | Security reason | Packet Trust Metadata V0 label |
| --- | --- | --- | --- | --- |
| `official_sec_clean.allowed.json` | official regulatory | allowed packet | Trusted official provenance with clean scan. | `trusted_provenance` |
| `official_sec_prompt_injection.blocked.json` | official regulatory | blocked | Trusted provenance still fails prompt-injection scanning. | `prompt_injection_blocked` |
| `fred_clean.allowed.json` | official macro | allowed packet | Trusted official macro provenance with clean scan. | `trusted_provenance` |
| `reddit_single_source_hype.quarantined.json` | social/community | quarantined | Single-source social heat is not evidence. | `unverified_social_heat` |
| `reddit_two_corroborations.allowed.json` | social/community | allowed packet | Social source has clean scan and two synthetic public corroborations. | `unverified_social_heat` |
| `reddit_duplicate_hype.quarantined.json` | social/community | quarantined | Duplicate hype has fewer than two useful corroborations. | `unverified_social_heat` |
| `discord_rumor.quarantined.json` | social/community | quarantined | Public community rumor lacks corroboration. | `unverified_social_heat` |
| `unknown_blog.quarantined.json` | unknown public blog | quarantined | Unknown source starts quarantined without corroboration. | `new_source_needs_corroboration` |
| `unknown_clean_two_corroborations.allowed.json` | unknown public blog | allowed packet | Unknown source has clean scan and two synthetic public corroborations. | `new_source_corroborated` |
| `news_watch_clean.quarantined_or_watch.json` | public news/watch | quarantined/watch | Watch source does not become truth without corroboration. | `watch_source_needs_corroboration` |
| `coindesk_watch_with_corroboration.allowed.json` | public market info/watch | allowed packet | Watch source has clean scan and two synthetic public corroborations. | `watch_source_corroborated` |
| `kalshi_odds_move_watch.quarantined_or_watch.json` | prediction market/watch | quarantined/watch | Odds move is context, not truth, without corroboration. | `odds_move_watch` |
| `polymarket_odds_move_with_corroboration.allowed.json` | prediction market/watch | allowed packet | Odds/watch source has clean scan and two synthetic public corroborations. | `odds_move_watch` |
| `raw_private_text_attempt.blocked.json` | attempted private text | blocked | Private-text export attempt is blocked before packet rendering. | `private_text_blocked` |

```text
tests/fixtures/coinfox_packet_soak/
```

The `unknown_clean_two_corroborations.allowed.json` fixture verifies that an unknown source
is not permanently blocked. Unknown sources start quarantined, but a clean unknown public
source with at least two independent corroborations can influence packet rendering after
prompt-injection scanning passes.

## Packet Trust Metadata V0

Packet Trust Metadata V0 now emits sanitized labels from this matrix:

```powershell
python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_soak\unknown_clean_two_corroborations.allowed.json --trust-metadata
```

The unknown-clean-two-corroborations case receives `new_source_corroborated`. Unknown
sources without enough corroboration receive `new_source_needs_corroboration`, and watch
sources without enough corroboration receive `watch_source_needs_corroboration`.

The `future_packet_trust_label_candidate` fixture field is kept for compatibility with the
original soak matrix naming, but it now mirrors the V0 label expected by
`tests/security/test_packet_trust_metadata_v0.py`.

No confidence labels, source scores, source reliability updates, or CoinFox UI presentation
were added in this pass.
