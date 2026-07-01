# FoxClaw Commands

Last updated: 2026-07-01.

This is the operator command map for `C:\Users\brend\dev\foxclaw-core`.

The fastest command menu is:

```powershell
python tools\foxclaw_commands.py
```

To open it in a new PowerShell window:

```powershell
.\tools\open_foxclaw_command_window.ps1
```

The Desktop shortcut named `FoxClaw Command Center` points at:

```powershell
.\tools\foxclaw_command_center_window.ps1
```

## Daily Start

```powershell
python tools\foxclaw_commands.py --run status
python tools\foxclaw_commands.py --run gym
python tools\foxclaw_commands.py --run a1-intake
python tools\foxclaw_commands.py --run source-discovery
python tools\foxclaw_commands.py --run interaction-potential
python tools\foxclaw_commands.py --run ledger-record-demo
python tools\foxclaw_commands.py --run ledger-verify-receipts
```

## Find Commands

```powershell
python tools\foxclaw_commands.py --list-ids
python tools\foxclaw_commands.py --search packet
python tools\foxclaw_commands.py --category coinfox_packets
python tools\foxclaw_commands.py --show interaction-potential
python tools\foxclaw_commands.py --all-tools
python tools\foxclaw_commands.py --json
```

## Safe Run Pattern

Run a curated command by ID:

```powershell
python tools\foxclaw_commands.py --run <command-id>
```

Manual-only commands are shown but not run by the command center. Those usually have
placeholder paths or write local staging files. Review the path first, then run the shown
command yourself.

## CoinFox Packet Flow

```powershell
python tools\foxclaw_commands.py --run a1-intake
python tools\foxclaw_commands.py --run source-discovery
python tools\foxclaw_commands.py --run interaction-potential
python tools\foxclaw_commands.py --run packet-demo-trust
python tools\foxclaw_commands.py --run coinfox-coordination-demo
```

Useful packet/security demos:

```powershell
python tools\foxclaw_commands.py --run packet-demo
python tools\foxclaw_commands.py --run coinfox-coordination-demo
python tools\foxclaw_commands.py --run ledger-record-demo
python tools\foxclaw_commands.py --run ledger-review-queue
python tools\foxclaw_commands.py --run unknown-corroborated-packet
python tools\foxclaw_commands.py --run prompt-injection-block
python tools\foxclaw_commands.py --run odds-watch-packet
```

## Validation

```powershell
python tools\foxclaw_commands.py --run focused-packet-tests
python tools\foxclaw_commands.py --run full-tests
python tools\foxclaw_commands.py --run invariants
python tools\foxclaw_commands.py --run diff-check
```

## All Current Tool Scripts

The command center discovers these directly from `tools/`:

| Tool | Help command |
| --- | --- |
| `tools\apollo_courier.py` | `python tools\apollo_courier.py --help` |
| `tools\apollo_mesh.py` | `python tools\apollo_mesh.py --help` |
| `tools\apollo_node_brief.py` | `python tools\apollo_node_brief.py --help` |
| `tools\apollo1_intake.py` | `python tools\apollo1_intake.py --help` |
| `tools\check_invariants.py` | `python tools\check_invariants.py --help` |
| `tools\coinfox_packet_demo.py` | `python tools\coinfox_packet_demo.py --help` |
| `tools\coinfox_coordination_demo.py` | `python tools\coinfox_coordination_demo.py --help` |
| `tools\export_public_intelligence.py` | `python tools\export_public_intelligence.py --help` |
| `tools\export_public_scorecard.py` | `python tools\export_public_scorecard.py --help` |
| `tools\forecast_desk_doctor.py` | `python tools\forecast_desk_doctor.py --help` |
| `tools\forecast_desk_export_public.py` | `python tools\forecast_desk_export_public.py --help` |
| `tools\forecast_desk_replay.py` | `python tools\forecast_desk_replay.py --help` |
| `tools\forecast_desk_scoreboard.py` | `python tools\forecast_desk_scoreboard.py --help` |
| `tools\forecast_desk_self_funding.py` | `python tools\forecast_desk_self_funding.py --help` |
| `tools\forecast_desk_sync.py` | `python tools\forecast_desk_sync.py --help` |
| `tools\forecast_desk_watch.py` | `python tools\forecast_desk_watch.py --help` |
| `tools\forecast_evidence_intake.py` | `python tools\forecast_evidence_intake.py --help` |
| `tools\forecast_learning_spine.py` | `python tools\forecast_learning_spine.py --help` |
| `tools\foxclaw_commands.py` | `python tools\foxclaw_commands.py --help` |
| `tools\foxclaw_gym.py` | `python tools\foxclaw_gym.py --help` |
| `tools\foxclaw_visitor_guide.py` | `python tools\foxclaw_visitor_guide.py --help` |
| `tools\freeze_db_schema.py` | `python tools\freeze_db_schema.py --help` |
| `tools\freeze_forecast_db_schema.py` | `python tools\freeze_forecast_db_schema.py --help` |
| `tools\interaction_potential.py` | `python tools\interaction_potential.py --help` |
| `tools\kalshi_api_desk.py` | `python tools\kalshi_api_desk.py --help` |
| `tools\ledger_list_receipts.py` | `python tools\ledger_list_receipts.py --help` |
| `tools\ledger_record_demo.py` | `python tools\ledger_record_demo.py --help` |
| `tools\ledger_review_queue.py` | `python tools\ledger_review_queue.py --help` |
| `tools\ledger_verify_receipt.py` | `python tools\ledger_verify_receipt.py --help` |
| `tools\microscope.py` | `python tools\microscope.py --help` |
| `tools\microscope_batch.py` | `python tools\microscope_batch.py --help` |
| `tools\public_intelligence_card_demo.py` | `python tools\public_intelligence_card_demo.py --help` |
| `tools\redshift_paper_boundary.py` | `python tools\redshift_paper_boundary.py --help` |
| `tools\render_public_intelligence_card.py` | `python tools\render_public_intelligence_card.py --help` |
| `tools\source_discovery_inventory.py` | `python tools\source_discovery_inventory.py --help` |

## Hard Boundary

The command catalog carries no live authority:

```text
can_submit_order=false
can_move_funds=false
live_execution_allowed=false
can_publish_to_coinfox=false
can_change_truth=false
can_change_source_reliability=false
can_update_verified_memory=false
can_train_model=false
can_run_live_network=false
```
