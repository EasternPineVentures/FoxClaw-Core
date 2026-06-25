# CoinFox Discord Reset Operator Checklist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the existing private Discord into an invite-safe CoinFox public server while preserving founder, signal, image, attachment, and origin-history material in a verified private archive.

**Architecture:** This is an operator runbook, not application code. The Discord server is converted in place after a local archive package is created, checksummed, and reviewed. Cleanup is blocked by explicit delete gates, role visibility tests, bot review, and a soft launch.

**Tech Stack:** Discord server settings, local encrypted storage outside git, PowerShell checksum verification, Markdown/CSV archive metadata, manual permission testing.

---

## Optional Read-Only Bot Helper

`tools/coinfox_discord_archive.py` can help with archive metadata, channel export,
attachment download, checksums, and stop-gate reporting.

Safety boundary:

- bot token only through `COINFOX_DISCORD_BOT_TOKEN`;
- legacy `USER_TOKEN` is ignored;
- no self-bot behavior;
- no channel deletion, movement, locking, creation, or invite creation;
- no token values printed in reports.

Commands:

```powershell
python tools\coinfox_discord_archive.py --archive-root C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24 doctor
python tools\coinfox_discord_archive.py --archive-root C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24 snapshot --guild-id <guild_id>
python tools\coinfox_discord_archive.py --archive-root C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24 export-channel --channel-id <channel_id> --bucket signal-history
python tools\coinfox_discord_archive.py --archive-root C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24 checksum
python tools\coinfox_discord_archive.py --archive-root C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24 verify
python tools\coinfox_discord_archive.py --archive-root C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24 stop-gate
```

## Optional Live Reset Bot Helper

`tools/coinfox_discord_reset.py` can help after Phase 3 is verified. It is not a
delete tool.

Safety boundary:

- bot token only through `COINFOX_DISCORD_BOT_TOKEN`;
- no self-bot behavior;
- no channel deletion;
- explicit commands only for permission doctor, invite revocation, and reset
  structure creation;
- `setup-structure` requires the bot role to have `Manage Channels`;
- `revoke-invites` requires the bot role to have `Manage Server`;
- `seed-first-pins` requires `Send Messages`, `Manage Messages`, and
  `Read Message History`;
- no token values printed in reports.

Commands:

```powershell
python tools\coinfox_discord_reset.py --guild-id <guild_id> doctor
python tools\coinfox_discord_reset.py --guild-id <guild_id> revoke-invites
python tools\coinfox_discord_reset.py --guild-id <guild_id> setup-structure
python tools\coinfox_discord_reset.py --guild-id <guild_id> rename-server --name CoinFox
python tools\coinfox_discord_reset.py --guild-id <guild_id> hide-legacy-surface
python tools\coinfox_discord_reset.py --guild-id <guild_id> seed-first-pins
```

Expected `setup-structure` behavior:

- creates private `PRIVATE OPS` category if missing;
- creates `founder-vault`, `mod-room`, and `reset-staging` private channels if missing;
- denies `View Channel` for `@everyone` on `PRIVATE OPS`;
- creates the public V4 categories/channels if missing:
  `COINFOX DEN`, `MARKET GYM`, `FOXCLAW INTEL`, `BUILD LAB`, `FIELD GUIDE`,
  and `SUPPORT`;
- does not move, lock, or delete legacy channels.

Expected `hide-legacy-surface` behavior:

- skips `COINFOX DEN`, `MARKET GYM`, `FOXCLAW INTEL`, `BUILD LAB`,
  `FIELD GUIDE`, `SUPPORT`, and `PRIVATE OPS`;
- denies `View Channel` for `@everyone` on legacy categories and channels where
  Discord permissions allow it;
- reports per-channel failures instead of aborting the whole pass;
- does not delete, rename, or move legacy channels;
- requires a fresh snapshot/visibility check after running, because child
  channels may still be hidden by a patched parent category even when Discord
  refuses a direct child-channel patch.

Expected `seed-first-pins` behavior:

- posts and pins the first public launch notes in `welcome`, `rules`,
  `trade-ideas`, `public-intel`, and `help-desk`;
- skips a launch note if a pinned message with the same `CoinFox Launch Note`
  marker already exists;
- reports posted, skipped, and missing-channel counts;
- does not create invites, edit roles, move channels, delete channels, or touch
  legacy content.

## Optional Mention-Only Representative Bot

`tools/coinfox_discord_rep.py` runs the CoinFox bot as a public-channel
representative. It is mention-only and dry-run by default.

Safety boundary:

- only channels listed in the JSON allowlist are polled;
- no private archive files are read;
- no `PRIVATE OPS`, raw feed, parser log, bot log, or old signal
  channel should appear in the allowlist;
- live posting requires `--send`;
- no trade advice, trade execution, signal parsing, moderation automation, or
  public invite creation.

Dry run:

```powershell
python tools\coinfox_discord_rep.py --channels-config config\coinfox_discord_public_channels.local.json
```

Live send:

```powershell
python tools\coinfox_discord_rep.py --channels-config config\coinfox_discord_public_channels.local.json --send
```

Keep `config\coinfox_discord_public_channels.local.json` out of git if it
contains live Discord channel IDs.

Discord setup requirements:

- the bot must be invited to the server with read access to the channels being archived;
- `Read Message History` is required for channel export;
- message content and attachment metadata may be empty unless the app has the
  required Message Content Intent enabled in the Discord Developer Portal;
- if `snapshot` cannot read invites, record invite state manually in
  `settings\invites-before-reset.md`.

## Stop Line

Run Phase 1 through Phase 3 first:

1. Freeze invites and permissions.
2. Archive founder, signals, images, files, and history.
3. Verify checksums.

Do not create a new public invite, delete channels, lock channels, move channels,
or publicly restructure legacy channels until Phase 3 is complete and the
archive evidence passes.

## Files And Artifacts

**Repo files:**

- Existing spec: `docs/superpowers/specs/2026-06-24-coinfox-discord-reset-design.md`
- This checklist: `docs/CoinFox_Discord_Reset_Operator_Checklist.md`

**Local archive root outside git:**

- Suggested path: `C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24`
- This path must stay outside `C:\Users\fox1i\Desktop\FoxClaw-Core-master`.
- If the suggested path is not encrypted by the local machine setup, place the same folder structure inside an encrypted container or encrypted external volume before exporting private content.

**Archive package contents:**

- `README.md`
- `manifest.json`
- `channel_decision_tracker.csv`
- `founder-footnotes.md`
- `redaction-log.md`
- `checksums.sha256` after Phase 3 verification
- `exports\founder-notes\`
- `exports\signal-history\`
- `exports\important-decisions\`
- `exports\pins\`
- `exports\server-snapshot\`
- `media\screenshots\`
- `media\charts\`
- `media\docs\`
- `media\brand-assets\`
- `settings\`

## Delete Gate

No channel may be deleted until all of these are true:

- [ ] The channel appears in `manifest.json`.
- [ ] The channel export file exists locally.
- [ ] `checksums.sha256` includes the channel export file.
- [ ] `checksums.sha256` includes saved image and media files for the channel.
- [ ] Checksum verification passes.
- [ ] The founder/operator confirms the channel has no obvious missing attachments, images, screenshots, charts, or docs.
- [ ] The channel appears in `channel_decision_tracker.csv`.
- [ ] The channel has been moved to `PRIVATE OPS / reset-staging` or marked pure clutter.

## Channel Decision Tracker

Create `channel_decision_tracker.csv` with this exact header:

```csv
channel_name,category,archive_status,pins_saved,attachments_saved,decision,public_after_reset,notes
```

Allowed values:

- `archive_status`: `not_started`, `exported`, `verified`, `skipped_pure_clutter`
- `pins_saved`: `yes`, `no`, `none_found`
- `attachments_saved`: `yes`, `no`, `none_found`
- `decision`: `keep_public`, `move_founder_vault`, `move_reset_staging`, `lock_then_delete`, `delete_after_verified`, `review_later`
- `public_after_reset`: `public`, `private_founder_vault`, `private_staging`, `deleted`

## Phase 1: Freeze Invites And Permissions

**Purpose:** Stop new people from entering while the server is still private-history shaped.

- [ ] Open Discord server settings and review active invite links.
- [ ] Revoke all old invite links.
- [ ] Confirm no active public invite remains.
- [ ] Do not create the new public invite yet.
- [ ] Review the current admin list.
- [ ] Remove admin from any account that should not control the reset.
- [ ] Confirm the founder/operator account has full control.
- [ ] Record the admin list in `settings\admin-list.md`.
- [ ] Record the current role list in `settings\roles-before-reset.md`.
- [ ] Record the current bot list in `settings\bots-before-reset.md`.
- [ ] Record the current category and channel list in `settings\channels-before-reset.md`.
- [ ] Record invite changes and any access freeze notes in `manifest.json` notes or `redaction-log.md`.
- [ ] Create the local archive root outside git.
- [ ] Create the Phase 1-3 folder buckets under `exports\`, `media\`, and `settings\`.
- [ ] Create an empty `README.md` in the archive root.
- [ ] Create an empty `redaction-log.md` in the archive root.
- [ ] Create `channel_decision_tracker.csv` with the required header.
- [ ] Create `manifest.json` with archive status `phase_1_3_archive_in_progress`.

PowerShell setup command:

```powershell
$ArchiveRoot = "C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24"
New-Item -ItemType Directory -Force -Path `
  $ArchiveRoot, `
  "$ArchiveRoot\exports\founder-notes", `
  "$ArchiveRoot\exports\signal-history", `
  "$ArchiveRoot\exports\important-decisions", `
  "$ArchiveRoot\exports\pins", `
  "$ArchiveRoot\exports\server-snapshot", `
  "$ArchiveRoot\media\screenshots", `
  "$ArchiveRoot\media\charts", `
  "$ArchiveRoot\media\docs", `
  "$ArchiveRoot\media\brand-assets", `
  "$ArchiveRoot\settings" | Out-Null
Set-Content -Encoding utf8 -Path "$ArchiveRoot\README.md" -Value "# CoinFox Discord Private Archive`n`nCreated: 2026-06-24`nPurpose: Founder, signal, image, attachment, and origin-history archive before CoinFox public reset.`n"
Set-Content -Encoding utf8 -Path "$ArchiveRoot\redaction-log.md" -Value "# Redaction Log`n`nRecord omitted credentials, private identifiers, unsafe screenshots, and other deliberate exclusions here without copying private values.`n"
Set-Content -Encoding utf8 -Path "$ArchiveRoot\channel_decision_tracker.csv" -Value "channel_name,category,archive_status,pins_saved,attachments_saved,decision,public_after_reset,notes"
@'
{
  "archive_name": "CoinFox_Discord_Archive_2026-06-24",
  "created_for": "CoinFox Discord reset",
  "status": "phase_1_3_archive_in_progress",
  "contains_private_material": true,
  "public_safe": false,
  "git_tracked": false,
  "checksum_file": "checksums.sha256",
  "notes": [
    "Phase 1-3 only: freeze invites, export/archive, fill manifest/tracker, verify checksums.",
    "No channel cleanup or public invite creation before archive verification."
  ],
  "channels": []
}
'@ | Set-Content -Encoding utf8 -Path "$ArchiveRoot\manifest.json"
```

Expected result:

```text
Archive root exists outside git with README.md, redaction-log.md, manifest.json,
channel_decision_tracker.csv, exports\, media\, and settings\.
```

## Phase 2: Archive Founder, Signals, Images, Files, And History

**Purpose:** Preserve the company memory before any cleanup.

- [ ] Export founder/operator chats and notes into `exports\founder-notes\`.
- [ ] Export signal channels and signal-adjacent discussion into `exports\signal-history\`.
- [ ] Export important decisions into `exports\important-decisions\`.
- [ ] Export important pinned messages into `exports\pins\` or `settings\pins-before-reset.md`.
- [ ] Save server snapshot exports into `exports\server-snapshot\`.
- [ ] Save all important attachments into the matching `media\` folder.
- [ ] Save screenshots into `media\screenshots\`.
- [ ] Save chart images into `media\charts\`.
- [ ] Save docs into `media\docs\`.
- [ ] Save the server icon, banner, channel imagery, and brand assets into `media\brand-assets\`.
- [ ] Save server settings screenshots or notes into `settings\server-settings-before-reset.md`.
- [ ] Save role screenshots or notes into `settings\roles-before-reset.md`.
- [ ] Save bot screenshots or notes into `settings\bots-before-reset.md`.
- [ ] Save invite screenshots or notes into `settings\invites-before-reset.md`.
- [ ] Save relevant moderation and trust-boundary notes into `settings\trust-boundary-notes.md`.
- [ ] Update `manifest.json` with every exported channel, date range, export file path, saved media path, and export method.
- [ ] Update `channel_decision_tracker.csv` for every reviewed channel.
- [ ] Update `founder-footnotes.md` with private creation notes worth preserving.
- [ ] Update `redaction-log.md` with anything deliberately omitted.

Minimum `manifest.json` shape:

```json
{
  "archive_name": "CoinFox_Discord_Archive_2026-06-24",
  "created_for": "CoinFox Discord reset",
  "status": "phase_1_3_archive_in_progress",
  "contains_private_material": true,
  "public_safe": false,
  "git_tracked": false,
  "checksum_file": "checksums.sha256",
  "channels": []
}
```

For each exported channel, add an object to `channels` with this shape:

```json
{
  "channel": "original-channel-name",
  "category": "original-category-name",
  "date_range": "oldest exported message date through newest exported message date",
  "export_file": "exports/original-channel-name.ext",
  "media_path": "media/original-channel-name",
  "pins_saved": "yes",
  "attachments_saved": "yes",
  "export_method": "manual Discord export or named export tool",
  "decision_tracker_status": "exported"
}
```

Use real channel names, paths, and dates in the archive copy. Do not commit the filled archive to git.

Expected result:

```text
Founder, signals, important pins, images, files, server settings, role list, bot list, and origin footnotes are present in the local archive root.
```

## Phase 3: Verify Checksums

**Purpose:** Prove the archive can be trusted before cleanup starts.

- [ ] Run checksum generation only after Discord exports and important media have been saved.
- [ ] Generate `checksums.sha256` over all archive files except `checksums.sha256` itself.
- [ ] Verify `checksums.sha256`.
- [ ] Confirm `checksums.sha256` exists and has content.
- [ ] Open a sample of channel exports locally.
- [ ] Open a sample of saved images and attachments locally.
- [ ] Confirm `manifest.json` references the expected exported channels.
- [ ] Confirm `channel_decision_tracker.csv` has a row for each reviewed legacy channel.
- [ ] Confirm the founder/operator sees no obvious missing attachments, images, screenshots, charts, or docs.
- [ ] Stop here before channel cleanup.

Generate checksums:

```powershell
$ArchiveRoot = "C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24"
Push-Location $ArchiveRoot
Get-ChildItem -Recurse -File |
  Where-Object { $_.Name -ne "checksums.sha256" } |
  Sort-Object FullName |
  ForEach-Object {
    $Hash = Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName
    $Relative = (Resolve-Path -Relative $_.FullName).TrimStart(".\")
    "{0}  {1}" -f $Hash.Hash.ToLowerInvariant(), $Relative
  } |
  Set-Content -Encoding utf8 "checksums.sha256"
Pop-Location
```

Verify checksums:

```powershell
$ArchiveRoot = "C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24"
$Failures = @()
Get-Content "$ArchiveRoot\checksums.sha256" | Where-Object { $_.Trim() } | ForEach-Object {
  $Parts = $_ -split "\s+", 2
  $Expected = $Parts[0]
  $Relative = $Parts[1]
  $Path = Join-Path $ArchiveRoot $Relative
  if (-not (Test-Path -LiteralPath $Path)) {
    $Failures += "MISSING $Relative"
  } else {
    $Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected) {
      $Failures += "MISMATCH $Relative"
    }
  }
}
if ($Failures.Count -gt 0) {
  $Failures
  exit 1
}
"Checksum verification passed"
```

Expected result:

```text
Checksum verification passed
```

Confirm checksum file exists and has content:

```powershell
Set-Location "C:\Users\fox1i\CoinFox_Discord_Archive_2026-06-24"
Get-Item .\checksums.sha256
Get-Content .\checksums.sha256 | Select-Object -First 10
```

Hard stop:

```text
Do not start Phase 4 until checksum verification passes and the founder/operator confirms the archive has no obvious missing images, attachments, pins, charts, or docs.
```

## Stop Gate Before Cleanup

Do not delete, lock, move, or publicly restructure channels until all are true:

- [ ] Archive folder has Discord exports.
- [ ] Important pins are saved.
- [ ] Important media is saved.
- [ ] `manifest.json` is updated.
- [ ] `channel_decision_tracker.csv` is updated.
- [ ] `checksums.sha256` is generated.
- [ ] Archive opens locally.
- [ ] Founder/operator can find founder footnotes without Discord.
- [ ] No public invites are active.

## Phase 4: Create Private Ops

**Purpose:** Create private Discord holding areas before public restructuring.

- [ ] Create category `PRIVATE OPS`.
- [ ] Create channel `founder-vault`.
- [ ] Create channel `mod-room`.
- [ ] Create channel `reset-staging`.
- [ ] Make `PRIVATE OPS` invisible to New, Member, and Moderator unless the moderator is explicitly trusted.
- [ ] Make `founder-vault` visible only to Founder and explicitly trusted internal collaborators.
- [ ] Test with a non-admin account or trusted helper.

Expected result:

```text
PRIVATE OPS exists, is private, and is ready for founder notes, moderation, and
legacy-channel review.
```

## Phase 5: Move Questionable Channels Into Staging

**Purpose:** Avoid accidental deletion while old channels are reviewed.

- [ ] Move questionable legacy channels into `PRIVATE OPS / reset-staging`.
- [ ] Lock channels that need review.
- [ ] Mark pure clutter in `channel_decision_tracker.csv`.
- [ ] Do not delete any channel unless every delete-gate item passes.
- [ ] Move only curated creation footnotes into `PRIVATE OPS / founder-vault`.

Expected result:

```text
Legacy channels are either staged, locked, vaulted, public-kept, or marked pure clutter.
```

## Phase 6: Build Public CoinFox Categories

**Purpose:** Make the server clearly public-facing and CoinFox-shaped.

- [ ] Use `COINFOX DEN`, not `THE DEN`; it is the brand/community compromise between corporate clarity and clubhouse feel.
- [ ] Use `FIELD GUIDE`, not `THE FOXHOLE`; it replaces the earlier `LEARN` naming with practical survival material.
- [ ] Create `COINFOX DEN` with `welcome`, `rules`, `announcements`, `general`, and `product-updates`.
- [ ] Create `MARKET GYM` with `market-talk`, `trade-ideas`, `risk-desk`, `good-signal-bad-trade`, and `postmortems`.
- [ ] Create `FOXCLAW INTEL` with `public-intel`, `no-edge-rejects`, and `paper-notes`.
- [ ] Create `BUILD LAB` with `testing-ground`, `feedback-and-ideas`, and `community-events`.
- [ ] Create `FIELD GUIDE` with `beginner-questions`, `risk-management`, and `before-you-click`.
- [ ] Create `SUPPORT` with `help-desk` only.
- [ ] Do not create `ARENA` at launch.
- [ ] Confirm `bot-feedback`, `bug-reports`, `roles`, `glossary`, and `forecast-reviews` are deferred, not deleted forever.
- [ ] Confirm New and Member roles see only public categories.

Expected result:

```text
The public channel surface reads as CoinFox V4, feels like a clubhouse, and
keeps PRIVATE OPS hidden.
```

## Phase 7: Add First Pinned Posts

**Purpose:** Give the public server its identity before anyone joins.

Optional helper:

```powershell
python tools\coinfox_discord_reset.py --guild-id <guild_id> doctor
python tools\coinfox_discord_reset.py --guild-id <guild_id> seed-first-pins
```

- [ ] Pin welcome.
- [ ] Pin rules.
- [ ] Pin risk disclaimer.
- [ ] Pin signals are not trades.
- [ ] Pin how to use trade-ideas.
- [ ] Pin what FoxClaw public intelligence means.
- [ ] Pin Week 1 games schedule when soft launch begins.
- [ ] Pin help-desk.

Welcome:

```text
CoinFox Launch Note: Welcome

Welcome to CoinFox.

CoinFox is a social trading and prediction discussion community built around structured ideas, receipts, risk discipline, and learning from outcomes.

Nothing here is financial advice. No post is a command to trade. A good signal is not automatically a good trade.

FoxClaw may generate public-safe ideas, paper-only notes, or postmortems here. These are for research and learning. Risk labels matter.

The Market Remembers. Receipts over hype.
```

Rules:

```text
CoinFox Launch Note: Rules

1. Keep public discussion respectful and useful.
2. Do not post private keys, account credentials, personal documents, or sensitive screenshots.
3. Label speculation clearly.
4. No spam, pump campaigns, impersonation, or paid promotion without disclosure.
5. Respect risk. Challenge ideas with reasoning, not personal attacks.
6. PRIVATE OPS and archived material stay private unless founder-approved and redacted.
```

Risk disclaimer:

```text
CoinFox Launch Note: Risk Disclaimer

CoinFox is for education, research, journaling, and public market discussion.

Nothing in this Discord is financial, investment, tax, legal, or trading advice. Markets can move fast, losses are possible, and every person is responsible for their own decisions.

Treat every idea as incomplete until you have your own plan, invalidation level, position sizing, and risk limit.
```

Signals are not trades:

```text
CoinFox Launch Note: Signals Are Not Trades

A signal is an idea, not an order.

A trade requires context: account risk, entry plan, invalidation, timeframe, liquidity, and whether the idea still makes sense when price changes.

Post ideas clearly. Separate observation from conviction. If the plan changes, say so.
```

How to use trade-ideas:

```text
CoinFox Launch Note: How To Use Trade Ideas

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

What FoxClaw public intelligence means:

```text
CoinFox Launch Note: FoxClaw Public Intelligence

FoxClaw public intelligence means public-safe market observations, research notes, risk labels, and no-edge reviews that can be discussed without exposing private founder material.

It is not a private signal feed. It is not a trading command system. It is paper-only unless clearly marked otherwise. No raw FoxClaw internals, raw private Discord history, private source content, or live trade commands belong here.
```

Help-desk:

```text
CoinFox Launch Note: Help Desk

Use help-desk for access questions, confusing server behavior, broken links, reports, or safety concerns.

Do not post passwords, private keys, account numbers, or sensitive screenshots. If something needs founder review, say what happened and keep private details out of public chat.
```

Expected result:

```text
All first pinned posts exist before any soft-launch invite is created.
```

## Phase 8: Review, Disable, Or Remove Bots

**Purpose:** Prevent old automation from seeing or leaking private material.

- [ ] Disable or permission-review every bot.
- [ ] Remove any parser bot from the public server surface.
- [ ] Remove any old signal bot from the public server surface.
- [ ] Remove admin from every bot unless explicitly required.
- [ ] Confirm no bot can see `PRIVATE OPS / founder-vault` unless founder-approved.
- [ ] Confirm no bot can see archive exports, staged private channels, or old logs unless documented.
- [ ] Record final bot decisions in `settings\bots-after-reset.md` in the local archive.

Expected result:

```text
No bot has surprise access to private history or public admin power.
```

## Phase 9: Test Role Visibility

**Purpose:** Make permissions the launch gate.

- [ ] Test as New.
- [ ] Test as Member.
- [ ] Test as Moderator.
- [ ] Test as Trusted Internal.
- [ ] Test as Founder.
- [ ] Confirm New cannot see `PRIVATE OPS`.
- [ ] Confirm Member cannot see `PRIVATE OPS`.
- [ ] Confirm Moderator cannot see `PRIVATE OPS` unless explicitly trusted.
- [ ] Confirm no public role sees legacy private channels.
- [ ] Confirm no public role sees archive exports.
- [ ] Confirm no public role sees bot, parser, or log channels.
- [ ] Confirm no public role sees `PRIVATE OPS / reset-staging`.
- [ ] Confirm invite route lands in `COINFOX DEN / welcome`.

Expected result:

```text
New public members can see only the intended public CoinFox surface.
```

## Phase 10: Revoke Old Invites And Create One Soft-Launch Invite

**Purpose:** Make one controlled doorway for the first invite wave.

- [ ] Revoke every old invite again.
- [ ] Confirm no old invite remains active.
- [ ] Create one new invite after permissions pass.
- [ ] Set the invite to land in `COINFOX DEN / welcome`.
- [ ] Use this invite only for the soft launch.

Expected result:

```text
There is one active soft-launch invite, and it lands users in COINFOX DEN / welcome.
```

## Phase 11: Invite 3 To 10 Trusted People

**Purpose:** Test the real join experience before broader public invites.

- [ ] Review `docs/superpowers/specs/2026-06-25-coinfox-week-1-community-games-design.md`.
- [ ] Invite 3 to 10 trusted people.
- [ ] Ask what channels they can see.
- [ ] Ask what feels confusing.
- [ ] Ask what feels too trading-heavy.
- [ ] Ask whether the server feels safe and understandable.
- [ ] Ask whether any old private material is visible.
- [ ] Run Week 1 community games manually inside existing public channels.
- [ ] Place Prediction Duels in `MARKET GYM / market-talk`.
- [ ] Place Good Signal, Bad Trade Court in `MARKET GYM / good-signal-bad-trade`.
- [ ] Place No-Edge Challenge in `FOXCLAW INTEL / no-edge-rejects`.
- [ ] Place Postmortems in `MARKET GYM / postmortems`.
- [ ] Place the weekly game schedule in `COINFOX DEN / announcements`.
- [ ] Do not create an `ARENA` category during Week 1.
- [ ] Do not use profit-only leaderboards or real-money contest framing.
- [ ] Review participation, moderation burden, channel clutter, safety issues, and user feedback.
- [ ] Record findings in `settings\soft-launch-feedback.md` in the local archive.

Expected result:

```text
Trusted invitees report no private visibility issues, identify any confusing
public copy or channel names, and generate enough Week 1 feedback to decide
whether an ARENA category is justified later.
```

## Phase 12: Fix Issues Before Broader Public Invite

**Purpose:** Launch wider only after the soft-launch feedback is handled.

- [ ] Fix role visibility issues.
- [ ] Fix confusing channel names.
- [ ] Fix pinned copy gaps.
- [ ] Remove or lock any accidentally visible old material.
- [ ] Re-test New and Member visibility.
- [ ] Confirm the archive remains private and outside git.
- [ ] Create broader public invite only after fixes pass.

Expected result:

```text
CoinFox Discord is invite-safe for broader public use.
```

## Rollback Rule

If anything feels wrong:

- [ ] Stop cleanup.
- [ ] Turn off public invites.
- [ ] Lock questionable channels.
- [ ] Do not delete more channels.
- [ ] Recheck permissions.
- [ ] Use the archive package and `PRIVATE OPS / reset-staging` to recover context.

## Self-Review Coverage

- Spec requirement: one Discord in-place conversion. Covered by Phases 1, 4, 6, 10.
- Spec requirement: founder-plus-signals archive. Covered by Phases 2 and 3.
- Spec requirement: images and media saved. Covered by Phases 2 and 3.
- Spec requirement: no deletion before archive verification. Covered by Stop Line, Delete Gate, and Phase 3 hard stop.
- Spec requirement: Private Ops, founder-vault, mod-room, and reset-staging. Covered by Phase 4.
- Spec requirement: public CoinFox categories. Covered by Phase 6.
- Spec requirement: first pinned public copy. Covered by Phase 7.
- Spec requirement: bot freeze. Covered by Phase 8.
- Spec requirement: role visibility test. Covered by Phase 9.
- Spec requirement: invite reset. Covered by Phase 10.
- Spec requirement: soft launch and Week 1 manual games. Covered by Phase 11.
- Spec requirement: broader public invite only after fixes. Covered by Phase 12.
