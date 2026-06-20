# Discord Parser Fixture Policy

Status: planning contract foundation.
Machine identity: A1.
Source repo path: C:\Users\brend\dev\foxclaw-core.
Branch: planning/parser-compatibility-v0.
Anchor commit: 85deb62d7e11f3d440c87eed37e7df88379b5996.

## Fixture Classes

### PRIVATE_LOCAL

Private local fixtures may contain the minimum sensitive content required for
parity. They are ignored, local-only, and never pushed.

Allowed location:

```text
tests/fixtures/parser_private/
runtime_private/parser_replay/
```

Rules:

- keep outside cloud-sync paths;
- encrypt at rest if practical;
- include safe metadata and hashes in manifests;
- never commit raw message bodies, source names, Discord IDs, links, invites, or
  token fragments;
- never paste private fixture contents into chat.

### SANITIZED_COMMITTABLE

Committed fixtures must be synthetic or fully redacted.

Allowed location:

```text
tests/fixtures/parser_v1/
tests/fixtures/internal_contract/
```

Required exclusions:

- no usernames;
- no user, server, channel, guild, or message IDs;
- no private source names;
- no Discord message links;
- no Discord invite links;
- no private quotations;
- no tokens, secrets, API keys, passwords, or prompt text from private systems;
- no raw private message body;
- no internal prompts or hidden model instructions.

## Required Categories Later

A2 fixture evidence should eventually cover:

```text
accepted
rejected
context_only
malformed
duplicate
missing_stop
missing_target
multiple_targets
edited_message
deleted_message
provider_timeout
provider_invalid_json
provider_error
unsupported_symbol
ambiguous_direction
prompt_injection_attempt
```

If A2 cannot prove a category exists in v1, mark it:

```text
UNKNOWN_PENDING_A2_INVENTORY
```

## Committed Fixture Metadata

Every generated report, manifest, fixture summary, parity output, and staging
artifact must include:

- machine identity;
- UTC timestamp;
- source repo path;
- branch;
- commit hash;
- tool or script name when generated.

## Safety Checks

Committed fixtures must pass private-source scanning and schema validation.
Validation failures should expose field paths, not private values.
