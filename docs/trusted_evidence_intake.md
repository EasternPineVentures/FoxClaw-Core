# Trusted Evidence Intake V1

FoxClaw is a decision matrix first. Trusted people may feed the matrix, but they do
not become the matrix.

This intake lane lets founder-approved contributors submit public evidence packets for
Forecast Desk markets. A packet can add context to a dossier after validation. It cannot
set an independent probability, publish a forecast, open a paper position, submit an
order, move funds, or grant authority to another system.

## Trust Boundary

Trusted means:

- the submitter is known to FoxClaw;
- the submitter is allowed to submit context;
- their packets are retained with submitter, market, source, claim, and hash lineage.

Trusted does not mean:

- their claim is accepted without validation;
- their claim can override banned classifications;
- their packet can supply a probability, side, verdict, sizing, or publication decision;
- their packet can authorize execution.

The code enforces this with `TrustedSubmitter`, `EvidencePacket`, and
`IntakeValidation`. The only default authority level is `context_only`.

## Packet Contract

Each evidence packet needs:

- `market_id`
- `url`
- `claims`
- optional `source_id`, `title`, `source_type`, `source_classification`, and
  `independence_group`

The packet is rejected before storage if it includes authority fields such as
`probability`, `independent_probability`, `side`, `verdict`, `can_publish`,
`can_enter_paper`, `can_submit_order`, `can_move_funds`, or `live_execution_allowed`.

After normalization, validation applies the same public-evidence rules as dossiers:

- public HTTP(S) source required;
- nonpublic, insider, hacked, classified, private, leaked, stolen, or access-bypassed
  information rejected;
- duplicate independence groups do not add a second dossier source.

## Ledger Tables

Schema version `3` adds:

- `trusted_evidence_packets`
- `trusted_evidence_validations`

Packets are stored separately from validations so FC can preserve the submission trail
while still rejecting bad, duplicate, or nonpublic inputs before they enter the dossier
queue.

## CLI

Fixture smoke test:

```powershell
python tools\forecast_evidence_intake.py --fixture --db .\data\forecast_desk.db --json
```

Manual submission:

```powershell
python tools\forecast_evidence_intake.py `
  --db .\data\forecast_desk.db `
  --submitter-id trusted-analyst-1 `
  --display-name "Trusted Analyst 1" `
  --market-id KXFOOTBALL-EXAMPLE `
  --url https://example.invalid/public-source `
  --source-type official `
  --source-classification public `
  --claim "Official public report confirms the relevant availability note." `
  --json
```

The CLI is a local operator tool. It is not authentication, not a public submission
endpoint, and not a live authority path.

## Football Use

Football can be a strong Forecast Desk wedge because the evidence surface is broad:
injury reports, depth charts, weather, travel, coaching changes, market movement, official
league notices, and schedule context. This lane gives trusted contributors a clean way to
submit those inputs while keeping FoxClaw's probability and decision layers independent.

## Redshift Boundary

Redshift can feed context as a protected research lane when explicitly routed that way.
Its role here is evidence or context submission only. Redshift context has no capital
effect, no order permission, and no authority to change Forecast Desk decisions.
