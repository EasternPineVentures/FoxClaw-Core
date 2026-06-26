# FoxClaw Apollo Node Brief

From: `A2`
To: `A1`
Role: `operator`
Generated: `2026-06-26T16:42:18Z`

## Repo

- Path: `C:\Users\fox1i\Desktop\FoxClaw-Core-master`
- Version: `0.4.16`
- Branch: `feature/parser-compat-v0`
- Head: `63c6a55` - docs: refine CoinFox Discord V4 launch layout
- Upstream: `origin/feature/parser-compat-v0`
- Ahead/behind: `17/6`
- Tree: `dirty`
- Changed files:
  - `M .gitignore`
  - ` M config/coinfox_discord_public_channels.example.json`
  - ` M docs/CoinFox_Discord_Reset_Operator_Checklist.md`
  - ` M docs/superpowers/plans/2026-06-25-coinfox-discord-representative-bot.md`
  - ` M foxclaw/adapters/discord/reset.py`
  - ` M tests/unit/test_coinfox_discord_reset.py`
  - ` M tools/coinfox_discord_reset.py`
  - `?? docs/handoffs/a2_render_fc_weekend_handoff_2026-06-26.md`
  - `?? docs/render_static_site_deploy.md`
  - `?? render.yaml`
  - `?? tests/unit/test_public_demo_site.py`
  - `?? tools/build_public_demo_site.py`

## Work

- Current slice: Render static FC demo and Discord cleanup handoff
- Next request: Commit separate slices, reconcile branch ahead/behind, push when safe, then connect Render using render.yaml
- Blockers: none
- Notes:
  - Static public demo builder added: tools/build_public_demo_site.py
  - Verification: pytest 367 passed, 1 skipped; check_invariants ok; public_site build ok
  - Manual Discord security remains: remove Administrator from CoinFox bot/app role

## Rails

- `pull_before_start`
- `commit_each_slice`
- `clean_tree_before_handoff`
- `do_not_overlap_dirty_files`
- `old_repo_reference_only`
- `no_secret_printing`
- `no_live_orders`
- `no_funds_movement`

## Authority

- `can_submit_order=false`
- `can_move_funds=false`
- `live_execution_allowed=false`
- `can_publish=false`
- `can_set_probability=false`
