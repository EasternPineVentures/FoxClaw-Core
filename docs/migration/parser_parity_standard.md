# Parser Parity Standard

Status: planning contract foundation.
Machine identity: A1.
Source repo path: C:\Users\brend\dev\foxclaw-core.
Branch: planning/parser-compatibility-v0.
Anchor commit: 85deb62d7e11f3d440c87eed37e7df88379b5996.

## Purpose

Parser parity compares v1 legacy parser behavior with the v2 compatibility
parser. It measures preservation before improvement.

Do not set required sample size or acceptable mismatch rate until A2 supplies
runtime evidence.

```text
required_sample_size = UNKNOWN_PENDING_A2_INVENTORY
acceptable_mismatch_rate = UNKNOWN_PENDING_A2_INVENTORY
```

## Comparison Record

Each parity record should include:

- machine identity;
- UTC timestamp;
- source repo path;
- branch;
- commit hash;
- fixture id or replay case id;
- raw event reference;
- parse attempt reference;
- accepted or rejected;
- candidate type;
- subject or symbol;
- direction or outcome;
- entry data;
- stop or invalidation;
- target data;
- time horizon;
- confidence;
- rejection reason;
- parser version;
- lineage relationships;
- duplicate disposition;
- mismatch class.

Duplicate disposition values:

```text
accepted_once
rejected_duplicate
merged_duplicate
unknown_review
```

## Mismatch Classes

```text
MATCH
EXPECTED_INTENTIONAL_DIFFERENCE
DATA_QUALITY_DIFFERENCE
PARSER_BEHAVIOR_REGRESSION
SECURITY_IMPROVEMENT
UNKNOWN_REVIEW
```

## Regression Examples

- accept becomes reject without documented reason;
- reject becomes accept without documented reason;
- direction or outcome changes;
- symbol or subject changes;
- entry, stop, invalidation, target, or time horizon semantics change;
- lineage breaks;
- duplicate behavior changes;
- provider failure becomes silent;
- private data crosses a public boundary;
- parser confidence becomes edge, risk, or execution authority.

## Security Improvement Examples

- prompt-injection-looking content remains rejected;
- raw private content is withheld where v1 exposed it;
- malformed provider output becomes explicit `ParserRejection`;
- user-token behavior is removed and replaced with bot-token-only architecture.

## Stop Line

If evidence is missing, classify it as `UNKNOWN_REVIEW`. Do not silently
normalize differences away and do not guess v1 behavior.
