# Forecast Learning Spine V1

FoxClaw becomes undeniable when learning is receipt-backed.

The V1 loop is:

```text
forecast receipt -> paper outcome -> learning receipt -> future review input
```

The learning receipt answers:

- what FoxClaw believed;
- what the market implied;
- what resolved;
- whether FoxClaw beat the market baseline;
- whether paper economics were profitable, flat, or losing;
- whether the next review signal is `reinforce`, `review`, `neutral`, or `void`.

## What V1 Does

`ForecastLearningReceipt` is a paper-only, public-information-only learning artifact.

It records:

- forecast probability;
- market YES baseline probability;
- forecast Brier score;
- market Brier score;
- Brier edge, calculated as `market_brier - forecast_brier`;
- paper net result;
- decision quality;
- learning signal.

Positive Brier edge means FoxClaw was better calibrated than the market baseline on that
resolved event. Negative Brier edge means the market baseline was better.

## What V1 Does Not Do

Learning receipts cannot:

- set future probability;
- submit orders;
- move funds;
- authorize live execution;
- mutate source trust automatically;
- publish themselves automatically.

They are memory and review input, not authority.

## Public-Safe Path

The receipt excludes founder-private reasoning and records only public-information learning
fields. A receipt can become a public-safe export candidate, but export remains a separate
policy decision.

That separation matters:

```text
Founder-private learning context stays private.
Public-safe proof can be deliberately distilled later.
```

## Operator Command

Fixture receipt:

```powershell
python tools\forecast_learning_spine.py --fixture --json
```

Record to a local Forecast Desk DB:

```powershell
python tools\forecast_learning_spine.py --fixture --db .\data\forecast_desk.db --json
```

The default fixture demonstrates a resolved paper forecast that outperformed the market
baseline and produced `learning_signal=reinforce`.
