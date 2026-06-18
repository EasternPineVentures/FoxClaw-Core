# Apollo Mesh V0

Apollo Mesh V0 is the founder-node substrate for A1, A2, and future founder FoxClaw nodes.

V0 is local-first and transport-neutral:

- FoxClaw owns the event schema.
- Nodes create signed, structured events.
- Each node keeps local append-only inbox/outbox logs.
- A relay, Nostr adapter, WebSocket service, or file transport can come later.

This gives the nodes a shared language now without making a public relay, blockchain, or
third-party dependency the architecture.

Apollo Mesh V0 is founder-only. See `docs/founder_node_security.md`.

## What V0 Can Share

Allowed event kinds:

- `node.heartbeat`
- `node.capability_manifest`
- `handoff.note`
- `runtime.alert`
- `context.receipt`
- `question.ask`
- `question.answer`
- `forecast.evidence`

These are information events. They can inform another node, but they cannot command it.

## Authority

Every Apollo Mesh event has hard false authority locks:

```text
can_submit_order=false
can_move_funds=false
live_execution_allowed=false
can_set_probability=false
can_remote_command=false
```

The content filter rejects command, order, funds, credential, token, secret, live order, and
account fields. A mesh event can carry context; it cannot carry power.

Every V0 event is also founder-private by default:

```text
node_role=founder_node
data_classification=founder_private
redistribution=do_not_export
public_export_allowed=false
```

Public/community nodes need a separate sanitized contract later. They do not attach to the
founder mesh.

## Signing

V0 uses stdlib HMAC-SHA256 over canonical JSON.

Identity is stored locally under `data/apollo_mesh/identity.json` by default. `data/` is
gitignored. The secret is never printed by the CLI.

This is deliberately a V0 private-mesh signature. It is enough for A1/A2 to prove event
integrity immediately. A later adapter can map this contract to public-key/Nostr-style
events without changing FoxClaw's internal payload model.

## Commands

Initialize a local identity:

```powershell
python tools\apollo_mesh.py --node-id A1 init
```

Emit a heartbeat:

```powershell
python tools\apollo_mesh.py --node-id A1 heartbeat --message alive --json
```

Emit a handoff:

```powershell
python tools\apollo_mesh.py `
  --node-id A1 `
  --json `
  handoff `
  --to-node A2 `
  --summary "Redshift boundary is ready" `
  --current-slice "apollo mesh v0" `
  --next-request "pull and send A2 heartbeat"
```

Receive a JSON event file into the verified inbox:

```powershell
python tools\apollo_mesh.py --node-id A2 --json receive --event-file .\handoff.json
```

Read inbox:

```powershell
python tools\apollo_mesh.py --node-id A2 --json inbox
```

Read outbox:

```powershell
python tools\apollo_mesh.py --node-id A2 --json inbox --log outbox
```

## A1 To A2 First Use

After pushing this version, A2 should run:

```powershell
git pull
python -m pytest tests\unit\test_apollo_mesh_events.py tests\regression\test_apollo_mesh_cli.py -q
python tools\apollo_mesh.py --node-id A2 init
python tools\apollo_mesh.py --node-id A2 --json heartbeat --message "A2 online"
```

Then paste the heartbeat JSON back to A1. Until relay transport exists, paste/file exchange is
the transport. The event format is the important part.

## Next Adapter

The next adapter should be one of:

- private Nostr-style relay mapping;
- FoxClaw-native WebSocket relay;
- file-drop transport for local network folders.

Do not build transport before the event contract stays green on A1 and A2.
