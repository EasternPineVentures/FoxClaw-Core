# Forecast Calibration

Status: Phase F foundation.

Forecast Desk calibration compares FoxClaw probabilities against resolved outcomes and the
market-implied baseline.

Core metrics:

```text
Brier score
Log loss
Market baseline Brier score
Net paper result after modeled costs
```

Lower Brier/log-loss is better. Paper profit without calibration is not proof; calibration
without cost-aware paper performance is not self-funding proof.
