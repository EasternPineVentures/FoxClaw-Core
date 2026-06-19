# FoxClaw Node Integration

Status: DEFERRED.
Owner repo: Future FoxClaw Node/mobile repository.
Upstream owner: EasternPineVentures/foxclaw-core.
Resume location: this file after quarantine and public contracts stabilize.
Tracking issue: EasternPineVentures/foxclaw-node#TBD.

## Purpose

Future nodes can validate claims, receipts, freshness, duplication, and market
snapshots. Nodes do not vote trades into existence.

## Nodes May Answer

- Did this source really publish this?
- Is this evidence still current?
- Did this event resolve?
- Is this post duplicated?
- Does this market snapshot match?

## Nodes Must Not Answer

- Should FoxClaw trade?
- How much capital should FoxClaw risk?
- Is this popular claim now true?
- Should source trust change directly?

## Deferred Ideas

Validator tasks, quarantine support, reputation-weighted corroboration, identity
recovery, and push notifications belong here, not inside unfinished CoinFox
internals.

## Resume Trigger

Resume only after public contracts, quarantine rules, and promotion receipts are
stable enough for untrusted or semi-trusted contributors.
