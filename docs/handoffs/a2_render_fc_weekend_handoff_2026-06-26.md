# A2 Weekend Handoff: Render + FC Demo

Date: 2026-06-26
From: A2 local working tree
Target: weekend testing while away from the main computer

## Current Goal

Make the FoxClaw public demo surface easy to test on Render without exposing private
FoxClaw internals.

The safe deploy target is a static site generated from public fixtures and the public
contract export.

## What Was Added

- `tools/build_public_demo_site.py`
- `tests/unit/test_public_demo_site.py`
- `render.yaml`
- `docs/render_static_site_deploy.md`

The builder creates:

```text
public_site/
  index.html
  styles.css
  README.txt
  coinfox-export/
    manifest.json
    intelligence_cards.jsonl
    scorecard.json
    outcomes.jsonl
```

`public_site/` is ignored by git. Render should generate it during build.

## Local Commands

Build the site:

```powershell
python tools\build_public_demo_site.py --output public_site
```

Focused verification:

```powershell
python -m pytest tests\unit\test_public_demo_site.py tests\regression\test_public_export.py -q
```

Demo gym check:

```powershell
python tools\foxclaw_gym.py --json
```

Threat-model read:

```powershell
Get-Content docs\security_public_demo_threat_model.md
```

## Render Settings

Use the checked-in `render.yaml`, or configure a Render Static Site manually:

```text
Build command:
python tools/build_public_demo_site.py --output public_site

Publish directory:
public_site
```

This is a testing/demo surface, not the final CoinFox product.

## Safety Boundary

Published:

- public fixtures
- public contract export
- paper-only card summaries
- outcome fixture

Never publish:

- `.env`
- local DB files
- Discord archives
- Apollo Mesh private data
- raw parser/private fixtures
- secrets
- live execution/account authority

## Current Verification Receipt

Focused tests passed:

```text
5 passed
```

Builder output:

```text
card_count=6
outcome_count=1
public_safe=true
paper_only=true
```

Gym status:

```text
readiness_status=training
demo_critical.blocked=0
demo_critical.ready=6
demo_critical.not_ready=4
```

## Git / Sync Warning

This branch is not clean and is also ahead/behind origin:

```text
feature/parser-compat-v0 ahead 17, behind 6
```

Do not assume Render can see these changes until they are committed and pushed.
Before pushing, reconcile the branch carefully from the machine that owns the current dirty
tree.

## Next Small Slice

1. Remove `Administrator` from the `CoinFox` bot/app role in Discord.
2. Commit the Discord cleanup and Render static demo changes as separate commits.
3. Pull/rebase or merge the `origin/feature/parser-compat-v0` changes.
4. Push the branch.
5. Connect Render to the branch and let `render.yaml` build `public_site`.
6. Show the site as the FoxClaw public-safe demo, then Discord as the CoinFox room.
