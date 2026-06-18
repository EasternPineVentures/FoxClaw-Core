# Kalshi API Field Guide

Status: Phase A read-only Forecast Desk notes, checked against Kalshi docs on 2026-06-18.

## Posture

FoxClaw uses Kalshi as a public market-data adapter. It does not create accounts, load
credentials, submit orders, move funds, or open WebSockets in Phase A.

Authority fields remain:

```text
CAN_SUBMIT_ORDER = false
CAN_MOVE_FUNDS = false
LIVE_EXECUTION_ALLOWED = false
DEFAULT_AUTHORITY_LEVEL = A4_prohibited
```

## REST Environments

Production REST:

```text
https://external-api.kalshi.com/trade-api/v2
```

Demo REST:

```text
https://external-api.demo.kalshi.co/trade-api/v2
```

The read-only API Desk defaults to production public market data and sends no auth headers.
Demo is named for later isolated rehearsal, not live execution.

## Public Discovery Endpoints

Initial Phase A surfaces:

```text
GET /series
GET /events
GET /markets
GET /markets/{ticker}
GET /markets/{ticker}/orderbook
GET /markets/trades
GET /historical/cutoff
GET /historical/markets
GET /historical/markets/{ticker}
```

List endpoints that return a `cursor` must be consumed as paginated data. The first page is
not the universe.

## Fixed-Point Doctrine

Kalshi current market-data values use fixed-point strings such as:

```json
["0.4200", "13.00"]
```

FoxClaw parses these as `Decimal`. Binary floats are rejected in normalized money, price,
probability, quantity, and book contracts.

## Order Book Reconstruction

Prediction market order books return YES bids and NO bids. Asks are reconstructed by
complementarity:

```text
best_yes_ask = 1 - best_no_bid
best_no_ask = 1 - best_yes_bid
```

The normalizer combines duplicate price levels, sorts bids best-first, preserves a raw
payload hash, and marks crossed or empty books as non-tradeable instead of pretending they
are executable.

## Historical Split

The historical cutoff endpoint defines which settled markets and older trade/fill history
must be queried from historical surfaces. Phase A stores this as a parser/routing contract;
later replay code will use it to avoid missing older markets.

## CLI

Offline fixture examples:

```powershell
python tools\kalshi_api_desk.py --fixture-dir tests\fixtures\kalshi doctor --json
python tools\kalshi_api_desk.py --fixture-dir tests\fixtures\kalshi markets --status open --limit 5 --json
python tools\kalshi_api_desk.py --fixture-dir tests\fixtures\kalshi orderbook --ticker KXJOBLESS-26JUN18-T250 --json
```

Live read-only smoke is opt-in outside the default suite:

```powershell
$env:FOXCLAW_KALSHI_INTEGRATION = "1"
python tools\kalshi_api_desk.py doctor --json
python tools\kalshi_api_desk.py markets --status open --limit 5 --json
```

No credential is required for these read-only commands.
