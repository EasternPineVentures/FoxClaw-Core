# FoxClaw / Redshift Paper Boundary

This note answers the current architecture question:

Should paper trading move to Redshift while FoxClaw stays the decision matrix?

## Recommendation

Do not move all paper trading to Redshift in one step.

Adopt this boundary first:

- FoxClaw owns decision matrix, evidence, policy, calibration, and durable receipts.
- Redshift may own market-specific research, paper execution experiments, and operational
  paper loops.
- Redshift does not own FoxClaw probability, policy, publication, or authority.
- Redshift sends paper execution and outcome receipts back to FoxClaw.

In short:

```text
FoxClaw decides and scores.
Redshift may rehearse paper execution.
Receipts connect them.
Authority stays locked.
```

## Why This Boundary

The old paper trading system may still be running and may still contain useful behavior. But
the clean repo is being built to avoid baggage. Moving the old paper system wholesale would
import unknowns, duplicate decision logic, and blur authority.

The safer move is a shadow boundary:

1. FoxClaw emits a paper-only decision receipt.
2. Redshift consumes the receipt as context.
3. Redshift simulates or paper-executes under its own paper lab rules.
4. Redshift emits a paper execution/outcome receipt.
5. FoxClaw ingests the outcome for scoring and calibration.

That lets us compare old and new paper behavior without deciding the permanent ownership too
early.

## Ownership Matrix

| Surface | Owner | Notes |
|---|---|---|
| Evidence eligibility | FoxClaw | Public information only. |
| Trusted contributor intake | FoxClaw | Context only, no probability authority. |
| Independent probability | FoxClaw | Decision matrix output. |
| Policy veto | FoxClaw | Final safety/paper/live boundary. |
| Forecast receipt | FoxClaw | Paper-only by default. |
| Market venue specifics | Adapter or Redshift | Must stay outside `engine/`. |
| Paper fill simulation | Shared candidate | FoxClaw can model it; Redshift can rehearse it. |
| Paper runtime loop | Redshift candidate | Only after receipt handshake is proven. |
| Outcome scoring | FoxClaw | Calibration and scoreboard stay with the matrix. |
| Live execution | No owner yet | Requires separate founder-approved authority phase. |

## Progress Gate

Paper trading should move toward Redshift only if a receipt handshake proves:

- FoxClaw decisions can be exported without private/internal fields;
- Redshift can consume the receipt without changing the decision;
- Redshift can emit paper execution/outcome receipts;
- FoxClaw can score those receipts;
- the old A2 paper runtime remains observable until shadow parity is acceptable;
- no live authority is introduced.

Until then, keep existing paper trading observable and reference-only.

## First Experiment

`Redshift Paper Boundary V1` is implemented as a small shadow experiment in:

- `foxclaw/adapters/redshift/paper_boundary.py`
- `tools/redshift_paper_boundary.py`
- `tests/unit/test_redshift_paper_boundary.py`
- `tests/regression/test_redshift_paper_boundary_cli.py`

Input:

- one FoxClaw `ForecastReceipt`;
- one public dossier hash;
- explicit costs;
- paper-only authority flags.

Output from Redshift or a Redshift-like adapter:

- `paper_execution_receipt_id`;
- linked `forecast_receipt_id`;
- fill price, size, slippage, fees, timestamp;
- no live order ID;
- no account ID;
- no funds movement;
- no execution authority.

Return path:

- FoxClaw stores the paper outcome or imports it into a scoring fixture.

Success:

- one deterministic fixture demonstrates the full receipt handshake;
- tests prove Redshift cannot mutate the FoxClaw decision fields;
- A1/A2 can run it without secrets.

Run it:

```powershell
python tools\redshift_paper_boundary.py --fixture --json
```

The fixture emits:

```text
FoxClaw ForecastReceipt
-> FoxClawDecisionExport
-> RedshiftPaperExecutionReceipt
-> RedshiftPaperOutcomeReceipt
```

All authority fields remain false, `redshift_capital_effect` is `none`, and no live order
or account identifiers are allowed.

## Decision To Defer

Do not decide permanent ownership of all paper trading yet.

After the first receipt handshake, choose one of three options:

1. FoxClaw keeps all paper simulation.
2. Redshift owns paper runtime loops and returns outcomes.
3. A shared adapter contract allows either node to rehearse paper execution.

The current preference is option 2 only if the receipt handshake is clean.
