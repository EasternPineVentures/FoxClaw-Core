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

## Shared Founder Mesh Enrollment

A local `init` or `heartbeat` proves that one node is online. It does not prove that A1 and
A2 can verify each other unless both identities were enrolled with the same founder mesh
secret.

The shared founder mesh secret is private security material:

- do not paste it into chat;
- do not commit it;
- do not send it through Apollo Mesh;
- keep any `--secret-file` outside git-tracked paths;
- compare only the public `key_id` returned by `doctor` or `rekey`.

Rekey A1 from a local secret file or `FOXCLAW_MESH_SECRET`:

```powershell
python tools\apollo_mesh.py --node-id A1 --json rekey --secret-file C:\path\outside\repo\founder_mesh_secret.txt
python tools\apollo_mesh.py --node-id A1 --json doctor
```

Repeat on A2 with the same secret moved through a secure local channel:

```powershell
python tools\apollo_mesh.py --node-id A2 --json rekey --secret-file C:\path\outside\repo\founder_mesh_secret.txt
python tools\apollo_mesh.py --node-id A2 --json doctor
```

If both `doctor` outputs show the same `key_id`, the nodes are enrolled in the same founder
mesh. The key ID is safe to compare; the secret is not.

`doctor` is read-only. If no identity exists yet, it reports `identity_exists=false` and
`secret_loaded=false` without creating `data/apollo_mesh/identity.json`.

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

`receive` accepts UTF-8, UTF-8-with-BOM, and UTF-16-with-BOM JSON files so Windows editor or
PowerShell formatting does not change the signature contract.

Read inbox:

```powershell
python tools\apollo_mesh.py --node-id A2 --json inbox
```

Read outbox:

```powershell
python tools\apollo_mesh.py --node-id A2 --json inbox --log outbox
```

## Private File-Drop Exchange

Manual paste proved the signature contract. The next connection layer is a private
file-drop exchange.

The exchange folder is transport only:

- each outbox event is written as one JSON file under `events/`;
- each node imports only peer events;
- duplicate events are skipped;
- malformed or wrongly signed files are counted as rejected;
- every event is still verified before entering the local inbox;
- no secrets, commands, orders, account IDs, funds movement, or authority flags are allowed.

Use a private folder that both founder nodes can reach. Good examples are a local network
share, a secure private sync folder, or a manual file-drop directory. Do not use GitHub,
public folders, committed repo paths, or public/community node infrastructure for the
founder mesh exchange.

Set the exchange folder with `--exchange-dir`:

```powershell
python tools\apollo_mesh.py `
  --node-id A1 `
  --exchange-dir C:\FoxClawFounderMesh `
  --json `
  pulse `
  --message "A1 pulse"
```

Or set it once per shell:

```powershell
$env:FOXCLAW_APOLLO_EXCHANGE_DIR = "C:\FoxClawFounderMesh"
python tools\apollo_mesh.py --node-id A1 --json pulse --message "A1 pulse"
python tools\apollo_mesh.py --node-id A1 --json sync
```

On A2, use the same exchange folder path as seen from that machine:

```powershell
$env:FOXCLAW_APOLLO_EXCHANGE_DIR = "C:\FoxClawFounderMesh"
python tools\apollo_mesh.py --node-id A2 --json pulse --message "A2 pulse"
python tools\apollo_mesh.py --node-id A2 --json sync
python tools\apollo_mesh.py --node-id A2 --json inbox
```

`pulse` is the normal active rhythm: emit heartbeat, export outbox, import verified peer
events. `sync` is the passive rhythm: export anything pending and import verified peer
events without creating a new heartbeat.

## A1 To A2 First Use

After pushing this version, A2 should run:

```powershell
git pull
python -m pytest tests\unit\test_apollo_mesh_events.py tests\regression\test_apollo_mesh_cli.py -q
python tools\apollo_mesh.py --node-id A2 --json doctor
python tools\apollo_mesh.py --node-id A2 --json heartbeat --message "A2 founder node online"
```

Then paste the heartbeat JSON back to A1. Until relay transport exists, paste/file exchange is
the transport. The event format is the important part.

If A2 initialized before the shared founder mesh secret was installed, run the rekey flow
above on both nodes before treating received events as cross-node verified.

## Next Adapter

The next adapter after the private file-drop exchange should be one of:

- private Nostr-style relay mapping;
- FoxClaw-native WebSocket relay;
- scheduled `pulse` / `sync` runners for A1 and A2.

Do not build transport before the event contract stays green on A1 and A2.
