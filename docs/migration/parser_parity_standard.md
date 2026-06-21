# Parser Parity Standard

Status: planning contract foundation.
Machine identity: A1.
Source repo path: C:\Users\brend\dev\foxclaw-core.
Branch: planning/parser-compatibility-v0.
Anchor commit: 85deb62d7e11f3d440c87eed37e7df88379b5996.

## Purpose

Parser parity compares v1 legacy parser behavior with the v2 compatibility
parser. It measures preservation before improvement. The v1 reference is the
A2-verified deterministic rule parser:

```text
live_raw_parser_admission_v13
src/parsers/signal_parser.py::parse_trade_signal
```

The compatibility threshold is strict for every replay case in the approved
fixture corpus: zero unexplained safety-relevant mismatches. Additional replay
volume can expand the corpus, but it cannot weaken the acceptance standard.

## Contract Package

A2 legacy replay emits one JSON object per line using:

```text
foxclaw/contract/internal/parser_legacy_result.schema.json
schema_version = parser_legacy_result.v1
```

A1 comparison emits:

```text
foxclaw/contract/internal/parser_parity_report.schema.json
schema_version = parser_parity_report.v1
```

Validation and comparison stay offline:

```powershell
python tools\validate_parser_legacy_results.py --jsonl C:\path\legacy_parser_results.jsonl --json
python tools\compare_parser_parity.py --legacy-jsonl C:\path\legacy_parser_results.jsonl --fixtures-dir C:\path\sanitized_replay_fixtures --json
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
- exact rejection reason when rejected;
- candidate type;
- subject or symbol;
- direction or outcome;
- entry data;
- quantity;
- stop or invalidation;
- target data;
- time horizon;
- confidence;
- rejection reason;
- parser version;
- lineage relationships;
- duplicate disposition;
- mismatch class.

Canonical numeric comparison is required for entry, quantity, stop, and target
fields. Formatting differences such as `"65000"`, `65000`, and `65000.0` may
match only after canonical decimal normalization.

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

## Intentional Differences

Every intentional difference must be documented with:

- fixture id or replay case id;
- old v1 behavior;
- new v2 behavior;
- safety classification;
- operator approval status.
