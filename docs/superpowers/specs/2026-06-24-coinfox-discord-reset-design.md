# CoinFox Discord Reset Design

Status: Approved for planning with external-review upgrades.
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
  decisions, pins, files, images, screenshots, and context before cleanup.
- Keep one founder-only vault for important creation footnotes and private
  reference material.
- Build a simple public CoinFox channel structure that supports conversation,
  trade ideas, questions, accountability, and future FoxClaw public intelligence.
- Remove or lock legacy clutter so the server feels like CoinFox, not a private
  prototype room with guests added.
- Treat cleanup as a controlled migration with a temporary staging area,
  rollback rule, role visibility test, and soft launch before wider invites.
- Track every legacy-channel decision before cleanup so archive status,
  attachments, pins, final visibility, and delete/lock/vault choices are explicit.

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
2. Create a portable local archive package with an index, channel decision
   tracker, and checksums.
3. Create a temporary reset-staging category before deleting or locking legacy
   channels.
4. Rebuild the existing Discord into the public CoinFox server.
5. Keep one founder-only vault category for important creation footnotes and
   private reference links.
6. Mostly empty, delete, or lock the old legacy channels after archive
   verification.
7. Test role visibility before any public invite.
8. Soft launch with a small trusted invite group before broader public invites.

This gives CoinFox an invite-safe home quickly while preserving the memory that
made the company real.

## Archive Scope

The archive standard is founder plus signals, not a full server museum.

Archive these categories before deletion:

- founder/operator chats and notes;
- signal channels and signal-adjacent discussion;
- pinned messages, attached files, images, screenshots, charts, and docs from
  important channels;
- company-origin decisions and narrative footnotes;
- server icon, banner, channel imagery, and any brand assets worth preserving;
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
- `channel_decision_tracker.csv` or `channel_decision_tracker.md` listing every
  reviewed legacy channel and its reset decision;
- `checksums.sha256` covering every exported file;
- `founder-footnotes.md` with curated private notes about the creation story;
- raw export files stored under clearly named channel folders;
- saved image and media files stored under clearly named channel folders, with
  filenames or sidecar notes that preserve their source channel and export date;
- a redaction log for anything deliberately omitted.

The archive should be useful later without requiring the old Discord server to
remain intact.

The channel decision tracker should use machine-friendly column names:

| Field | Required meaning |
| --- | --- |
| `channel_name` | Original channel name. |
| `category` | Original category name. |
| `archive_status` | `not_started`, `exported`, `verified`, or `skipped_pure_clutter`. |
| `pins_saved` | `yes`, `no`, or `none_found`. |
| `attachments_saved` | `yes`, `no`, or `none_found`. |
| `decision` | `keep_public`, `move_founder_vault`, `move_reset_staging`, `lock_then_delete`, `delete_after_verified`, or `review_later`. |
| `public_after_reset` | `public`, `private_founder_vault`, `private_staging`, or `deleted`. |
| `notes` | Short founder/operator note explaining the decision. |

## Server Shape

The converted CoinFox Discord should have a lean V4 public surface that can feel
alive with 5 to 15 people:

- `COINFOX DEN`
  - welcome
  - rules
  - announcements
  - general
  - product-updates
- `MARKET GYM`
  - market-talk
  - trade-ideas
  - risk-desk
  - good-signal-bad-trade
  - postmortems
- `FOXCLAW INTEL`
  - public-intel
  - no-edge-rejects
  - paper-notes
- `BUILD LAB`
  - testing-ground
  - feedback-and-ideas
  - community-events
- `FIELD GUIDE`
  - beginner-questions
  - risk-management
  - before-you-click
- `SUPPORT`
  - help-desk
- `PRIVATE OPS`
  - founder-vault
  - mod-room
  - reset-staging

`COINFOX DEN` is the brand/community compromise: clear enough to read as
CoinFox, warm enough to feel like a clubhouse rather than a corporate wiki. Use
`COINFOX DEN`, not `THE DEN`.

`FIELD GUIDE` replaces the earlier `LEARN` / `THE FOXHOLE` naming. It should feel
like practical survival material, not homework.

`SUPPORT` has only `help-desk` at launch. Keep reporting and help together until
there is enough volume to justify splitting them.

The following channels/categories are deferred, not deleted forever:
`bot-feedback`, `bug-reports`, `roles`, `glossary`, `forecast-reviews`, and
`ARENA`. Add them later only when usage proves they are needed.

`FOXCLAW INTEL` is curated and controlled at first. `public-intel`,
`no-edge-rejects`, and `paper-notes` should be founder/mod post-first channels;
members may react or discuss in threads later if the moderation load stays
healthy. It is not a raw public signal feed.

`PRIVATE OPS` is hidden from public roles. `founder-vault` preserves private
creation footnotes and archived decisions. `mod-room` is for moderation and
launch operations. `reset-staging` is a temporary holding area for old channels
before deletion, locking, or archival review.

## Roles And Permissions

Start with a minimal role model:

- Founder: full administration.
- Trusted Internal: access to founder vault and operational channels.
- Moderator: public moderation permissions without archive access.
- Member: normal public participation.
- New: limited posting until onboarding or anti-spam checks pass.

Public invites should land new users into `COINFOX DEN / welcome`. New users
should not see `PRIVATE OPS`, founder-vault material, archived exports, old
private channels, bot logs, parser logs, or raw signal history.

## Reset-Staging And Rollback

The cleanup order is:

```text
Archive -> verify checksum -> move to staging -> permission check -> delete or lock
```

Cleanup must not skip directly from archive creation to broad deletion. When a
legacy channel is questionable, move it into `PRIVATE OPS / reset-staging`, hide
it from public roles, and decide its fate after the archive and permissions are
verified.

If the reset gets messy:

1. Stop cleanup immediately.
2. Turn off public invites.
3. Lock questionable legacy channels.
4. Do not delete more channels.
5. Recheck permissions.
6. Use the archive package and staging category to recover context.

Rollback does not need to restore every old channel. It freezes the reset before
private material, permissions mistakes, or accidental deletion spreads.

## Cleanup Rules

Cleanup only begins after the archive package is created and checksum-verified.

No channel may be deleted until:

- it appears in `manifest.json`;
- its export file exists locally;
- `checksums.sha256` includes the export file and saved media files;
- checksum verification passes;
- the founder/operator confirms the channel has no obvious missing attachments,
  images, screenshots, charts, or docs;
- the channel appears in the channel decision tracker;
- the channel has been moved to `PRIVATE OPS / reset-staging` or marked pure
  clutter.

After verification:

- delete channels that are pure clutter and already archived;
- lock channels that need a short review window before deletion;
- move questionable channels to `PRIVATE OPS / reset-staging` before final
  deletion;
- move only essential origin notes into the founder vault;
- remove old invites that were meant for the private server;
- review bot permissions and remove bots not needed for the public CoinFox
  server;
- rename the server, categories, and onboarding copy to CoinFox;
- pin a concise public welcome and rules message before inviting outsiders.

The server should feel intentionally public, not like a private workspace with
some channels hidden.

## Bot Freeze

Before any public invite:

- disable or permission-review every bot;
- remove any parser bot from the public server surface;
- remove any old signal bot from the public server surface;
- remove admin from every bot unless that permission is explicitly required;
- confirm no bot can see `PRIVATE OPS / founder-vault` unless the
  founder/operator approves it;
- confirm no bot can see local archive exports, staged private channels, or
  hidden legacy logs unless there is a documented internal reason.

## Invite Reset

Before the soft launch:

1. Revoke every old invite.
2. Create one new invite after permissions pass.
3. Set the invite to land in `COINFOX DEN / welcome`.
4. Use that invite for the soft launch only.
5. Create broader public invites only after the soft-launch review is complete.

## Public Launch Copy

Write and pin the public-safe welcome, rules, risk disclaimer, and "signals are
not trades" explanation before cleanup finishes. This gives the rebuilt server a
target identity while old channels are being sorted.

The first pinned posts are required deliverables:

- welcome;
- rules;
- risk disclaimer;
- signals are not trades;
- how to use trade-ideas;
- what FoxClaw public intelligence means.
- Week 1 games schedule when soft launch begins.

Welcome copy:

```text
Welcome to CoinFox.

CoinFox is a social trading and prediction discussion community built around
structured ideas, receipts, risk discipline, and learning from outcomes.

Nothing here is financial advice.
No post is a command to trade.
A good signal is not automatically a good trade.

FoxClaw may generate public-safe ideas, paper-only notes, or postmortems here.
These are for research and learning. Risk labels matter.

The Market Remembers.
Receipts over hype.
```

Rules copy:

```text
1. No financial advice.
2. No guaranteed-profit claims.
3. No pump spam.
4. No private leaks, doxxing, hacked material, or stolen data.
5. Label risky ideas clearly.
6. Respect postmortems and losses.
7. Do not pressure people to trade.
8. Keep receipts when making claims.
9. No impersonation, fake screenshots, or fake performance.
10. Mods may remove anything that makes the community unsafe or misleading.
```

Trade-ideas guidance:

```text
Trade ideas must include:

- thesis
- timeframe
- invalidation
- risk
- what would change your mind

No "what do you think?" posts without a thesis.
No "buy now" posts.
No guaranteed-profit claims.
No pressure to copy trades.
A good signal is not automatically a good trade.
```

FoxClaw public safety language:

```text
CoinFox discussion is informational and educational.
Nothing is individualized financial advice.
FoxClaw public intelligence is paper-only unless clearly marked otherwise.
Risk labels matter.
No wallet/key requests.
No paid signal pressure.
No guaranteed-profit claims.
No pump spam.
```

## Public Story Rule

The archive is private source material. Public history must be curated.

The archive is not the public story. It is a private source vault that can later
support carefully redacted origin posts, founder notes, and screenshots. The
public Discord should show the curated CoinFox identity, not raw archive
material.

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

- confirm `PRIVATE OPS / founder-vault` is invisible to Member and New roles;
- confirm Moderator cannot see `PRIVATE OPS / founder-vault` unless the moderator is explicitly
  trusted for internal material;
- confirm old private channels are deleted, locked, or hidden;
- confirm invite links route users into the public onboarding path;
- confirm no raw signal channel remains public;
- confirm no credentials or private exports are attached in Discord;
- confirm no public role can see archive exports, bot logs, parser logs, or
  `PRIVATE OPS / reset-staging`;
- confirm all bots have been disabled or permission-reviewed;
- confirm no bot has admin unless explicitly needed;
- confirm old invites have been revoked and the one soft-launch invite lands in
  `COINFOX DEN / welcome`;
- confirm public rules state that CoinFox discussion is informational and not
  individualized financial advice.

Test visibility with a dummy account or trusted helper assigned to each role:
New, Member, Moderator, Trusted Internal, and Founder. The permissions test is
the launch gate, not a nice-to-have.

## Soft Launch

After cleanup and permission testing, invite 3 to 10 trusted people first. Ask
them:

- what they can see;
- what feels confusing;
- what feels too trading-heavy;
- whether the server feels safe and understandable;
- whether any old private material is visible.

Fix channel names, permissions, and pinned copy before broader public invites.

## Run Order

1. Freeze invites and permissions.
2. Archive founder, signals, images, files, and history.
3. Verify checksums.
4. Create `PRIVATE OPS` with `founder-vault`, `mod-room`, and `reset-staging`.
5. Move questionable channels into staging.
6. Build the V4 public CoinFox categories.
7. Add welcome, rules, disclaimer, and explainer pins.
8. Review, disable, or remove bots.
9. Test role visibility.
10. Revoke old invites and create one soft-launch invite.
11. Invite 3 to 10 trusted people.
12. Fix issues before broader public invite.

## Success Criteria

The reset is successful when:

- the archive package exists locally and passes checksum verification;
- the founder can find important creation footnotes without reopening old clutter;
- a new user can join the server without seeing private history;
- public channels clearly say CoinFox and support real discussion;
- the public surface follows the V4 layout and stays lean enough to feel alive
  with 5 to 15 people;
- the first small trusted invite group reports no private visibility issues;
- the old private Discord surface is mostly gone;
- future public storytelling can be curated from the archive without leaking raw
  private material.

## Planning Handoff

The implementation plan should produce an operator checklist, not code. It should
cover archive preparation, verification, server restructuring, permissions
testing, cleanup, and first-invite readiness.
