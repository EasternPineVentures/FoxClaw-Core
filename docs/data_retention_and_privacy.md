# Data Retention and Privacy

Status: Phase C foundation.

FoxClaw Forecast Desk stores only what it needs to reproduce public, paper-only decisions.

## Stored

- Public venue payloads and their raw hashes.
- Normalized public market snapshots.
- Public evidence metadata and public URLs.
- Resolution-source receipts.
- Paper-only decision-support receipts.

## Not Stored

- Private communications without permission.
- Material nonpublic information.
- Hacked, stolen, classified, doxxed, or access-bypassed material.
- API keys, private keys, account credentials, or wallet secrets.
- Production order credentials.

## Location

Forecast Desk databases and raw archives are node-local. Resolution order is explicit path,
then environment variable, then repo-local fallback under `data/`. Cloud-sync folders such as
OneDrive are rejected for authoritative Forecast Desk storage.

## Redaction Rule

Future public exports must publish only sanitized receipt fields. Raw payload archives stay
local unless a later reviewed publication policy explicitly marks fields safe.
