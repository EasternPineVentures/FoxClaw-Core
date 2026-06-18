# Paper Simulation Methodology

Status: Phase E foundation.

Forecast Desk paper simulation is a receipt exercise, not execution.

## Entry Price

Paper entries use executable top-of-book prices:

```text
YES entry price = best_yes_ask = 1 - best_no_bid
NO entry price  = best_no_ask  = 1 - best_yes_bid
```

The simulator does not use midpoint by default.

## Depth and Partial Fills

Available depth comes from the opposite bid side used to infer the ask:

```text
YES ask depth = depth at best NO bid
NO ask depth  = depth at best YES bid
```

If requested contracts exceed top-of-book depth, the receipt is marked `partial`.

## Fees

Every paper position records a fee-model version. Phase E defaults to an explicit-zero fee
model unless a schedule is supplied, so FoxClaw does not invent unknown live venue costs.

## Settlement

Paper settlement pays:

```text
1.00 per filled contract if side matches the resolved outcome
0.00 if side loses
entry cost back if void
```

Net result is payout minus entry cost minus recorded fees.

## No Lookahead

Replay refuses to settle a paper position against a resolution timestamp earlier than the
position open time. If this guard trips, the replay is invalid.
