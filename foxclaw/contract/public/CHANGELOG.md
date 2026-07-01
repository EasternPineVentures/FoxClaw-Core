# FoxClaw Public Intelligence Contract Changelog

## [1.0.0-additive] - 2026-07-01

Added the FoxClaw-CoinFox Coordination Contract V0 as an additive public-contract shape.

- `coinfox_coordination_packet.v0` supports `IntentPacket`,
  `CoordinationDecision`, `ActionReceipt`, and `OutcomeReceipt`.
- The contract records intent before action, explicit ack/block decisions, action/block
  receipts, and public engagement outcomes.
- The V0 demo is schema/fixture/tooling only and grants no production publish, trading,
  custody, lending, advice, private-evidence export, or live API authority.

## [1.0.0-additive] - 2026-06-27

Added the CoinFox curated packet schema as an additive public-contract shape.

- `coinfox_curated_packet.v1` supports `market_pulse_now`, `idea_board_now`, and
  `what_changed_since_yesterday` packet types.
- The packet carries public source links, source quality labels, public-safe summaries,
  counterpoints, suggested thesis angles, risk flags, and outcome-review prompts.
- The packet is review-priority-only and cannot expose private FoxClaw lineage, raw
  private content, live execution, or funds authority.

## [1.0.0] - 2026-06-19

Initial frozen public contract for CoinFox consumption.

- Public intelligence card v1.
- Public scorecard v1.
- Attention receipt v1.
- Risk classification v1.
- Verified outcome v1.

The contract is informational, paper-only, and not individualized advice.
Internal FoxClaw objects remain private and are not part of this public contract.
