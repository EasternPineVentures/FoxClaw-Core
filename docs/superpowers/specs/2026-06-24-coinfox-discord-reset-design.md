# CoinFox Discord Reset Design

Status: Approved for planning.
Date: 2026-06-24.
Owner: CoinFox founder/operator.
Repository context: `foxclaw-core` documents the boundary; Discord operations happen outside this repo.

## Context

The existing Discord started as a trusted private workspace for founder discussion,
signals, and early FoxClaw/CoinFox development. That history matters and should
be preserved, but the current server is not invite-safe for a public CoinFox
community.

The operator can support one Discord server. Therefore the reset is an in-place
conversion: the existing Discord becomes the CoinFox public server after the
important history is archived and the old channel surface is aggressively
cleaned.

FoxClaw remains the private decision engine and public-contract producer.
CoinFox is the public social surface. Raw private Discord history, private
source content, Discord identifiers, and unreviewed signal history must not be
published into CoinFox public channels.

## Goals

- Make the existing Discord safe to invite new CoinFox community members into.
- Preserve the company's origin story, founder notes, signal history, important
  decisions, pins, files, and context before cleanup.
- Keep one founder-only vault for important creation footnotes and private
  reference material.
- Build a simple public CoinFox channel structure that supports conversation,
  trade ideas, questions, accountability, and future FoxClaw public intelligence.
- Remove or lock legacy clutter so the server feels like CoinFox, not a private
  prototype room with guests added.

## Non-Goals

- Do not publish raw private messages or raw signal history.
- Do not treat archived signals as financial advice, verified performance, or
  public marketing claims.
- Do not connect a live Discord parser, bot-token migration, CoinFox API, or
  FoxClaw publishing path as part of this reset.
- Do not copy FoxClaw internals into CoinFox public channels.
- Do not rely on a second live Discord server.

## Chosen Approach

Use a clean public launch with one founder vault:

1. Export and verify a founder-plus-signals archive.
2. Create a portable local archive package with an index and checksums.
3. Rebuild the existing Discord into the public CoinFox server.
4. Keep one founder-only vault category for important creation footnotes and
   private reference links.
5. Mostly empty, delete, or lock the old legacy channels after archive
   verification.

This gives CoinFox an invite-safe home quickly while preserving the memory that
made the company real.

## Archive Scope

The archive standard is founder plus signals, not a full server museum.

Archive these categories before deletion:

- founder/operator chats and notes;
- signal channels and signal-adjacent discussion;
- pinned messages, attached files, screenshots, and docs from important channels;
- company-origin decisions and narrative footnotes;
- channel list, role list, bot list, and server settings snapshot;
- invite history if available;
- moderation or trust-boundary notes that explain why the reset happened.

Exclude or redact:

- credentials, token fragments, private keys, wallet data, and API keys;
- Discord user, server, channel, or message IDs from any public-facing summary;
- raw private-source names or private source quotes from public materials;
- doxxed, hacked, classified, stolen, or access-bypassed material;
- anything the operator would not want a future invited member to see.

## Archive Package

The first archive target is a local encrypted folder outside git. A later copy
to an external drive is allowed after the local package is verified.

The package should contain:

- `README.md` explaining what was archived, when, and why;
- `manifest.json` listing exported channels, date ranges, file counts, and export
  method;
- `checksums.sha256` covering every exported file;
- `founder-footnotes.md` with curated private notes about the creation story;
- raw export files stored under clearly named channel folders;
- a redaction log for anything deliberately omitted.

The archive should be useful later without requiring the old Discord server to
remain intact.

## Server Shape

The converted CoinFox Discord should have a small, legible public surface:

- `START HERE`
  - welcome
  - rules
  - announcements
  - roles
- `COINFOX`
  - general
  - market-talk
  - trade-ideas
  - questions
  - wins-losses-postmortems
- `FOXCLAW CONTEXT`
  - public-intelligence
  - paper-only-notes
- `SUPPORT`
  - help
  - reports
- `FOUNDER VAULT`
  - founder-footnotes
  - archived-decisions
  - signal-history-index

The `FOUNDER VAULT` category is private to the founder/operator and any explicitly
trusted internal collaborators. Public members cannot see it.

## Roles And Permissions

Start with a minimal role model:

- Founder: full administration.
- Trusted Internal: access to founder vault and operational channels.
- Moderator: public moderation permissions without archive access.
- Member: normal public participation.
- New: limited posting until onboarding or anti-spam checks pass.

Public invites should land new users into `START HERE`. New users should not see
founder vault channels, archived exports, old private channels, bot logs, parser
logs, or raw signal history.

## Cleanup Rules

Cleanup only begins after the archive package is created and checksum-verified.

After verification:

- delete channels that are pure clutter and already archived;
- lock channels that need a short review window before deletion;
- move only essential origin notes into the founder vault;
- remove old invites that were meant for the private server;
- review bot permissions and remove bots not needed for the public CoinFox
  server;
- rename the server, categories, and onboarding copy to CoinFox;
- pin a concise public welcome and rules message before inviting outsiders.

The server should feel intentionally public, not like a private workspace with
some channels hidden.

## Public Story Rule

The archive is private source material. Public history must be curated.

Allowed future public story material:

- a short "how CoinFox started" post;
- the principle that a signal is not a trade;
- the paper-only discipline behind FoxClaw context;
- lessons from building in public versus trusting private rooms;
- founder-approved screenshots only after redaction.

Disallowed public story material:

- raw private messages;
- raw signal calls presented as advice or performance proof;
- private usernames, IDs, links, or screenshots with unapproved people;
- claims that cannot point to a public-safe receipt, fixture, or status marker.

## Safety Checks

Before the first public invite:

- confirm the founder vault is invisible to Member and New roles;
- confirm old private channels are deleted, locked, or hidden;
- confirm invite links route users into the public onboarding path;
- confirm no raw signal channel remains public;
- confirm no credentials or private exports are attached in Discord;
- confirm public rules state that CoinFox discussion is informational and not
  individualized financial advice.

## Success Criteria

The reset is successful when:

- the archive package exists locally and passes checksum verification;
- the founder can find important creation footnotes without reopening old clutter;
- a new user can join the server without seeing private history;
- public channels clearly say CoinFox and support real discussion;
- the old private Discord surface is mostly gone;
- future public storytelling can be curated from the archive without leaking raw
  private material.

## Planning Handoff

The implementation plan should produce an operator checklist, not code. It should
cover archive preparation, verification, server restructuring, permissions
testing, cleanup, and first-invite readiness.
