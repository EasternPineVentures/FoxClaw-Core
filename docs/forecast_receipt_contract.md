# Forecast Receipt Contract

Status: Phase C foundation.

Forecast Desk receipts are public-evidence, paper-only decision-support artifacts. They may
explain why a market deserves attention, but they cannot authorize live action.

## Evidence Eligibility

Every evidence item receives an `EvidenceEligibilityVerdict` before it can enter a dossier.
Rejected classifications include:

```text
material_nonpublic
insider
hacked
classified
private_communication
doxxed
paywall_bypass
access_control_bypass
restricted
stolen
```

An LLM summary, user note, or page text cannot override this verdict. Evidence without a
public HTTP(S) URL is rejected.

## Dossier

An `EvidenceDossier` carries:

```text
market_id
resolution_rule_text
settlement_sources
allowed evidence
rejected evidence verdicts
duplicate evidence collapsed count
independence group count
contradiction count
evidence_quality
dossier_hash
can_authorize_execution=false
can_execute_trades=false
can_mutate_grove=false
```

Duplicate reporting is collapsed by `independence_group`, so repeated coverage of the same
underlying source does not masquerade as independent evidence.

## Resolution Quality

Paper entry is blocked when a market lacks either:

```text
resolution_rule_text
settlement_sources
```

The desk can watch ambiguous markets, but it cannot pretend they are clean paper candidates.

## Authority

All event-contract policy receipts keep:

```text
can_submit_order=false
can_move_funds=false
live_execution_allowed=false
authority_level=A4_prohibited
```
