# Source Discovery Inventory V0

Status: EXISTS.
Last updated: 2026-06-30.

## Purpose

Source Discovery Inventory V0 answers:

```text
Where should FoxClaw look first when preparing CoinFox packet ideas?
```

It is not the Source Registry. The inventory is a discovery map. The Source Registry remains
the policy layer that decides how an intake observation is treated before it can influence a
packet.

Inventory:

```text
config/source_discovery_inventory.json
```

Report command:

```powershell
python tools\source_discovery_inventory.py
python tools\source_discovery_inventory.py --json
```

## Fastest Practical Loop

For Apollo 1 manual-first work:

1. Check the source discovery report.
2. Pick one public item with a public link.
3. Capture what happened, why it matters, counterpoint, and outcome review question.
4. Add it to a packet intake worksheet.
5. Score interaction potential.
6. Run the packet demo with trust metadata.
7. Keep social/unknown sources quarantined unless they have two independent corroborations.

```powershell
python tools\source_discovery_inventory.py --limit 20
python tools\interaction_potential.py --intake tests\fixtures\coinfox_packet_intake\manual_market_pulse_intake.valid.json
python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_intake\manual_market_pulse_intake.valid.json --trust-metadata
```

## Source Families

The V0 inventory includes:

- CoinFox-native posts, theses, comments, challenges, and attention aggregates;
- Reddit communities;
- Stocktwits, X, YouTube, TikTok, newsletters, and public Discord surfaces;
- SEC, company investor relations, press releases, and earnings materials;
- FRED, BLS, BEA, Federal Reserve, Treasury, EIA, FINRA, CFTC, NYSE, Nasdaq, and Cboe;
- Reuters, AP, Bloomberg, CNBC, Yahoo Finance, Benzinga, Seeking Alpha, and TradingView;
- Kalshi, Polymarket, and forecast-community sources;
- CoinGecko, DefiLlama, Dune, Etherscan, Whale Alert, and other crypto/on-chain context;
- Google Trends, Wikipedia pageviews, GitHub, app rankings, job postings, patents, NOAA,
  and official sports injury reports.

This is a living seed map, not a claim that every useful source on the internet has been
exhaustively listed.

## Reddit First

Reddit is a major early-warning lane because retail attention, ticker narratives, option
ideas, crypto narratives, and public counterarguments often appear there quickly.

V0 breaks Reddit into individual discovery sources, including:

- `reddit_wallstreetbets`;
- `reddit_stocks`;
- `reddit_investing`;
- `reddit_stockmarket`;
- `reddit_options`;
- `reddit_daytrading`;
- `reddit_swingtrading`;
- `reddit_securityanalysis`;
- `reddit_valueinvesting`;
- `reddit_pennystocks`;
- `reddit_shortsqueeze`;
- `reddit_superstonk`;
- `reddit_dividends`;
- `reddit_bogleheads`;
- `reddit_algotrading`;
- `reddit_cryptocurrency`;
- `reddit_bitcoin`;
- `reddit_ethereum`;
- `reddit_cryptomarkets`;
- `reddit_solana`.

All Reddit sources are:

```text
trust_state = quarantined
source_type = social_community
requires_corroboration_count = 2
```

That means Reddit can tell FoxClaw what people are noticing. It cannot tell FoxClaw what is
true by itself.

## What To Capture

Every useful source item should become a small public-safe observation:

```text
source link
timestamp
asset/topic
what happened
why interesting
counterpoint
public-safe summary
corroborations
suggested CoinFox prompt
outcome review question
```

Then use Interaction Potential V0 to rank which observations are most likely to create
useful CoinFox comments, challenges, saves, and outcome-review returns:

```text
docs/interaction_potential_v0.md
```

Do not capture raw private chat, copied article bodies, credentials, private IDs, local file
paths, or trade instructions.

## Priority Rules

Start with:

1. CoinFox public posts and theses, once live.
2. Reddit and Stocktwits for attention spikes.
3. Official/company sources for corroboration.
4. Prediction markets for probability-change context.
5. Professional public news for event context.
6. Market/crypto/on-chain data for confirmation or contradiction.
7. Alternative attention/fundamental sources for slower thesis support.

Social heat plus an official/source corroboration plus market data is often enough to make a
CoinFox discussion prompt. It is not enough to make a trade recommendation.

## Deferred

Deferred until explicit review:

- automated Reddit ingestion;
- Discord parser/scalping;
- private community intake;
- live source automation;
- source reliability scoring;
- source reputation mutation;
- CoinFox publishing from FoxClaw.

The current A1 path is manual public discovery and packet review.

## Hard Rails

```text
can_submit_order = false
can_move_funds = false
live_execution_allowed = false
can_publish_to_coinfox = false
can_change_source_reliability = false
can_update_verified_memory = false
can_train_model = false
```
