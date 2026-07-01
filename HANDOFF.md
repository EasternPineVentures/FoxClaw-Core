# HANDOFF - foxclaw-core

This is the operational front door for the clean FoxClaw company repo.

Keep this file short. Move long historical phase logs into `docs/archive/` or the changelog.
Read this before changing code, then verify with `git log --oneline -10` and the commands below.

Last updated: 2026-07-01
Branch: `master`
Version: `0.4.16`
Working repo: `C:\Users\brend\dev\foxclaw-core`
Current proof baseline: `442 passed`, `check_invariants.py -> green`, `git diff --check -> green`

---

## 0. Start Here

At the start of any FoxClaw work session:

```powershell
cd C:\Users\brend\dev\foxclaw-core

git status
git log --oneline -10

python tools\foxclaw_commands.py --list-ids
python tools\foxclaw_gym.py --json
python tools\check_invariants.py
```

If you need the command launcher:

```powershell
.\tools\open_foxclaw_command_window.ps1
```

If the tree is dirty, do not start a new feature until you understand the uncommitted changes.

---

## 1. Project Truth

FoxClaw is the root system.

```text
FoxClaw = core decision/evidence/receipt engine
CoinFox = public community and market discussion layer
FCDB = technical data store
FoxClaw Ledger = receipt/proof/history layer
Apollo = founder/private core nodes only
Kinetic Grid = future user-powered node infrastructure
OmniNode = future user node client
OmniNode Scout = future mobile contribution mode
```

Short architecture:

```text
                         FOXCLAW
          Decision network / evidence engine / system authority
                             |
        +--------------------+--------------------+
        v                    v                    v
      FCDB            FOXCLAW LEDGER          COINFOX
 Technical DB       Receipts / proof      Public community UI
                             ^                    |
                             |                    v
                             |        Posts, sources, comments,
                             |        theses, challenges, outcomes
                             |                    |
                             +------------ feedback loop -------------+

                      KINETIC GRID
        Future user-powered contribution infrastructure
                             |
          +------------------+------------------+
          v                  v                  v
      APOLLO NODES      OMNINODE WORKER    OMNINODE SCOUT
      Founder core      Desktop/server     Mobile users
```

CoinFox is now a rough public beta at:

```text
https://coinfox.foxclaw.cloud/
```

CoinFox owns live product behavior: onboarding, posting, comments, votes, moderation, feed feel, deployment health, and UI presentation. FoxClaw supports CoinFox through public-safe contracts, leakage tests, curated packets, receipt exports, and boundary docs.

---

## 2. Active Lanes

### A. CoinFox support through public contracts

FoxClaw may create public-safe context for CoinFox, but must not reach into CoinFox internals.

Use:

```powershell
python tools\coinfox_packet_demo.py --fixture
python tools\coinfox_coordination_demo.py
```

Current contract boundary:

```text
IntentPacket -> CoordinationDecision -> ActionReceipt -> OutcomeReceipt
```

No live APIs. No auto-publishing. No private evidence export.

### B. FoxClaw Ledger V0

FoxClaw Ledger V0 is the local-only receipt/proof/history layer for coordination packets.

Package:

```text
foxclaw/ledger/
```

Docs:

```text
docs/ledger/foxclaw_ledger_v0.md
```

Tools:

```powershell
python tools\ledger_record_demo.py
python tools\ledger_list_receipts.py
python tools\ledger_verify_receipt.py
python tools\ledger_review_queue.py
```

Local receipt paths:

```text
runtime_logs/foxclaw_ledger/receipts.jsonl
runtime_logs/foxclaw_ledger/review_tasks.jsonl
```

V0 stores JSONL receipts and review tasks, verifies stable hashes, records blocked `auto_publish` attempts as blocked, and makes no live CoinFox API calls.

### C. Curated packet intake and anti-poisoning

Manual public-source observations can become reviewed packet cards only after intake guard checks.

Key files:

```text
docs/coinfox_curated_packet_intake.md
tests/fixtures/coinfox_packet_intake/manual_market_pulse_intake.valid.json
config/public_source_registry.json
tests/fixtures/coinfox_packet_soak/
```

Useful commands:

```powershell
python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_intake\manual_market_pulse_intake.valid.json --trust-metadata

python tools\coinfox_packet_demo.py --fixture --intake tests\fixtures\coinfox_packet_soak\unknown_clean_two_corroborations.allowed.json --trust-metadata
```

Rules:

- New or uncorroborated sources default to quarantine.
- Obvious prompt-injection phrases block even trusted sources.
- Public/social/Reddit/community sources stay quarantined until corroborated.
- Trust metadata is a review label, not a confidence score and not a source-reliability mutation.

### D. A1 standalone intake continuity

Apollo 1 can keep manual/public packet intake moving while Apollo 2 and the legacy Discord parser are unavailable.

Use:

```powershell
python tools\apollo1_intake.py --fixture --json
```

A2 legacy Discord parser inventory remains deferred and read-only. Do not block A1 manual packet work on A2.

### E. Source discovery and interaction potential

Use before each manual Market Pulse pass:

```powershell
python tools\source_discovery_inventory.py --fixture --json --limit 20
python tools\interaction_potential.py --fixture --json
python tools\foxclaw_commands.py --run interaction-potential
```

Interaction Potential ranks likely CoinFox discussion value. It carries no truth, evidence, source-reliability, publishing, trading, or memory-write authority.

### F. Forecast Desk / event-contract intelligence

Forecast Desk remains the implemented intelligence lane.

It is paper-only, read-only by default, and must stay under:

```text
foxclaw/adapters/event_contracts/
```

The neutral `engine/` must remain domain-neutral and free of Kalshi/event-contract vocabulary.

### G. Microscope V0

Microscope V0 is the private accepted-candidate assessment and safe local CoinFox staging bridge.

Use:

```powershell
python tools\microscope.py --list-recent
python tools\microscope.py --private-preview <args>
python tools\microscope_batch.py --dry-run
```

Do not run:

```powershell
python tools\microscope_batch.py --write-staging
```

against the live Grove/legacy DB until the legacy Discord parser inventory and publication-promotion gate are reviewed.

### H. Apollo Mesh founder-only

Apollo Mesh V0 is founder-only. Do not connect public/community nodes.

Use:

```powershell
python tools\apollo_mesh.py --node-id A1 --json pulse --message "A1 active"
python tools\apollo_mesh.py --node-id A1 --json sync
python tools\apollo_node_brief.py --node-id A1 --peer-node A2
```

Public/community nodes require a separate sanitized contract later.

### I. Apollo-1 local LLM, pending next safe infrastructure pass

Apollo-1 can become the local inference lighthouse after Ledger and authority receipts are stable.

First use cases only:

```text
log summaries
node health explanations
branch mismatch diagnosis
source/message classification
code review summaries
risk commentary, advisory only
```

Forbidden:

```text
trade execution
fund movement
secret rotation
direct Ledger mutation
public node direct access to Apollo-1
```

Recommended first engine:

```text
Ollama on Apollo-1
default local endpoint: http://127.0.0.1:11434/v1
starter model: qwen3:8b
network_exposed: false
```

---

## 3. Hard Rails

These are non-negotiable:

```text
CAN_SUBMIT_ORDER = false
CAN_MOVE_FUNDS = false
LIVE_EXECUTION_ALLOWED = false
DEFAULT_AUTHORITY_LEVEL = A4_prohibited
```

Also non-negotiable:

```text
no live order path
no account creation
no funds movement
no production credential load
no jurisdiction bypass
no LLM authority path
no private evidence export
no auto-publishing to CoinFox
no source score mutation from V0 trust metadata
no public/community Apollo Mesh access
```

Public information only.

---

## 4. Repo and Data Rules

- This repo is the clean migration target and public-ready work surface.
- Git is the handoff path.
- A1 and A2 are VS Code workstations on the same clean `foxclaw-core` repo.
- A2 may have an old FoxClaw checkout. Treat it as legacy/read-only unless a task explicitly says otherwise.
- OneDrive is not an authoritative runtime or database source.
- Do not put Forecast Desk DBs under OneDrive.
- No credentials, DB files, raw runtime logs, or private keys belong in git.
- Do not hardcode `C:\Users\brend\...` in code. Use explicit args, environment variables, then repo-local fallback.

---

## 5. Validation Commands

### Fast safety check

```powershell
python tools\check_invariants.py
git diff --check
```

### Full suite

```powershell
python -m pytest -q -p no:cacheprovider
```

Expected current proof:

```text
442 passed
python tools\check_invariants.py -> green
git diff --check -> green
```

### Coordination / Ledger focused check

```powershell
python -m pytest tests\unit\test_foxclaw_ledger_v0.py tests\unit\test_coinfox_coordination_contract.py tests\unit\test_public_contract_schemas.py tests\unit\test_foxclaw_command_center.py -q -p no:cacheprovider

python tools\coinfox_coordination_demo.py
python tools\ledger_record_demo.py --store runtime_logs\foxclaw_ledger\smoke_receipts.jsonl --review-queue runtime_logs\foxclaw_ledger\smoke_review_tasks.jsonl
python tools\ledger_verify_receipt.py --store runtime_logs\foxclaw_ledger\smoke_receipts.jsonl --json
```

Expected proof:

```text
39 passed
4 coordination packets emitted
4 receipts written
1 review task written
ledger verify valid true
```

### Packet / anti-poisoning focused check

```powershell
python -m pytest tests\security\test_packet_trust_metadata_v0.py tests\security\test_curated_packet_soak_fixtures_v0.py tests\security\test_source_registry_v0.py tests\security\test_anti_poisoning_v0.py -q -p no:cacheprovider
```

Expected proof:

```text
59 passed
```

---

## 6. Current High-Value Commands

```powershell
python tools\foxclaw_visitor_guide.py --fixture
python tools\foxclaw_gym.py --json
python tools\foxclaw_commands.py --list-ids
python tools\foxclaw_commands.py --run interaction-potential
python tools\source_discovery_inventory.py --fixture --json --limit 20
python tools\interaction_potential.py --fixture --json
python tools\coinfox_packet_demo.py --fixture
python tools\coinfox_coordination_demo.py
python tools\ledger_record_demo.py
python tools\ledger_review_queue.py
```

Use `foxclaw_commands.py` as the front door when unsure.

---

## 7. Recommended Next Work

Use `python tools\foxclaw_gym.py --json` at the start of each session and take the top `next_attention` item unless the operator gives a stronger priority.

Current best next slices:

### P0 - Commit and checkpoint

If the tree is dirty after recent Ledger/contract work, commit before new development.

Suggested commit message:

```text
Add FoxClaw Ledger V0 receipt layer
```

### P1 - Ledger Review Brief

Add a small operator-facing report that answers:

```text
What receipts exist?
Which are blocked?
Which need review?
What review tasks are due?
What should the operator inspect next?
```

Possible tool:

```text
tools/ledger_brief.py
```

This is a natural next step after Ledger V0.

### P2 - CoinFox support, not CoinFox internals

CoinFox product work belongs in the CoinFox repo. In `foxclaw-core`, only support it through:

```text
public-safe packet contracts
leakage tests
receipt exports
boundary docs
operator-reviewed intake
```

Do not build CoinFox UI, account flows, or moderation inside `foxclaw-core`.

### P3 - Apollo-1 Local LLM Probe

After Ledger V0 is committed and stable, add local-only Apollo-1 LLM probe support:

```text
config/fc_nodes.json
docs/local_llm_apollo1.md
tools/fc_local_llm_probe.py
```

Keep:

```text
network_exposed=false
advisory_only=true
no execution authority
all calls produce receipts later
```

### P4 - Source Reliability V1 later

Anti-Poisoning V1 Source Reliability should wait for one to two weeks of real curated packet data.

Do not add source score mutation before then.

---

## 8. Deferred / Do Not Start Yet

Do not start these until an explicit operator decision:

```text
NYFE paper exchange
real portfolio simulation
paper lending mechanics
Kinetic Grid public nodes
OmniNode client
blockchain/governance mechanics
live FoxClaw -> CoinFox API integration
CoinFox auto-publish
Kalshi demo auth / websocket work
live execution gate
source reliability mutation
public Apollo Mesh
```

Phase I is demo-only authentication and WebSocket rehearsal. It should not start unless demo credential boundaries are explicit.

Phase J is documentation-only live execution gate:

```text
kalshi/auth.py
kalshi/websocket.py
docs/runbooks/kalshi_demo.md
docs/live_execution_gate.md
```

---

## 9. A2 Return Plan

When Apollo 2 returns:

```powershell
git pull
python -m pytest -q -p no:cacheprovider
python tools\check_invariants.py
python tools\apollo_mesh.py --node-id A2 --json pulse --message "A2 active"
```

Then A2's isolated lane:

```text
read-only legacy Discord parser inventory
```

Inventory targets:

```text
active listener
parser entrypoints
credential classes
DB/file writes
providers/models
deduplication
watchdogs
obsolete-vs-active classification
sanitized fixture recommendations
```

Do not let A2 mutate the old repo. It is reference-only unless explicitly promoted.

---

## 10. Watch List

- Keep `engine/` free of Kalshi/event-contract vocabulary.
- Keep default tests offline and deterministic.
- Treat Kalshi docs as live; changelog drift must become a later receipt watcher.
- Do not expand Packet Trust Metadata V0 into confidence labels, source scoring, or memory mutation.
- Do not run source automation until trust/privacy boundaries are explicit.
- Keep `docs/first_encounter_guide.md` understandable without live explanation.
- Review `docs/security_public_demo_threat_model.md` before public demo/dry run.
- Keep FoxClaw from endlessly expanding around CoinFox. CoinFox is already live beta; FoxClaw should support it through contracts and receipts, not swallow it.

---

## 11. Handoff Update Rule

When updating this file:

1. Keep the top half operator-focused.
2. Put detailed phase history in a changelog/archive, not here.
3. Update:
   - `Last updated`
   - `Version`
   - `Current proof baseline`
   - `Active Lanes`
   - `Recommended Next Work`
4. Include exact commands and expected outputs.
5. Preserve the hard rails.
