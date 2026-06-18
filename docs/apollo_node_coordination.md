# Apollo Node Coordination V1

This is the coordination protocol for FoxClaw Apollo nodes, starting with A1 and A2.

It exists because two VSCode workstations can move fast only if they exchange crisp
receipts. A node brief is not authority, not runtime state, and not a shared database. It
is a signed-in-practice operator packet: current repo truth, current slice, next request,
blockers, and the rails that stay locked.

For structured node-to-node events, use Apollo Mesh V0 in `docs/apollo_mesh_v0.md`.
For founder-node IP/security posture, read `docs/founder_node_security.md`.

## Nodes

- A1: `C:\Users\brend\dev\foxclaw-core`
- A2: `C:\Users\fox1i\Desktop\FoxClaw-Core-master`

Both are clones of the same clean `foxclaw-core` repo. The old A2 FoxClaw checkout is
legacy/reference runtime unless explicitly touched.

## Tool

Generate a Markdown brief:

```powershell
python tools\apollo_node_brief.py `
  --node-id A1 `
  --peer-node A2 `
  --current-slice "Apollo node coordination V1" `
  --next-request "git pull, read docs\apollo_node_coordination.md, then run the old-repo inventory" `
  --note "Old A2 repo is reference-only" `
  --old-reference-path "C:\Users\fox1i\Desktop\FoxClaw"
```

Generate JSON:

```powershell
python tools\apollo_node_brief.py --node-id A2 --peer-node A1 --json
```

Write a local packet file:

```powershell
python tools\apollo_node_brief.py --node-id A1 --peer-node A2 --write .\data\apollo\a1_to_a2.md
```

`data/` is gitignored. Packet files are local operator artifacts unless deliberately pasted
into a handoff or issue.

## Mesh Tool

Generate a signed local mesh heartbeat:

```powershell
python tools\apollo_mesh.py --node-id A1 --json heartbeat --message alive
```

The event is founder-private by construction:

```text
node_role=founder_node
data_classification=founder_private
redistribution=do_not_export
public_export_allowed=false
```

Generate a signed local mesh handoff:

```powershell
python tools\apollo_mesh.py --node-id A1 --json handoff --to-node A2 `
  --summary "Slice complete" `
  --current-slice "apollo mesh v0" `
  --next-request "pull and send A2 heartbeat"
```

## Required Brief Contents

Every Apollo node brief includes:

- protocol: `apollo_node_brief_v1`
- sender and peer node IDs
- repo path, version, branch, head commit, upstream, ahead/behind count
- clean/dirty tree status and changed files
- current slice
- next request
- blockers and notes
- hard rails
- authority locks, all false

The tool never reads `.env`, prints secrets, opens old DBs, or inspects account credentials.

## Handoff Rhythm

Before moving work from A1 to A2:

1. Run the full relevant tests for the slice.
2. Commit the slice.
3. Confirm `git status --short --branch`.
4. Generate an Apollo brief from A1 to A2.
5. Push only when the slice is ready for A2 to pull.

When receiving work on A2:

1. `git pull`
2. `git status --short --branch`
3. `Get-Content VERSION`
4. Read the Apollo brief or `docs/a2_migration_context.md`.
5. Avoid editing files that the other node reports as dirty.

If either node is dirty, the other node should not overlap those files.

## Authority

Apollo node communication cannot authorize:

- live orders;
- funds movement;
- publishing;
- probability setting;
- account or credential work;
- old repo mutation.

All authority flags in `ApolloNodeBrief` are false by construction.

## Good A1 To A2 Message

```text
I pushed commit <sha>. Please pull, confirm VERSION, run:

python tools\apollo_node_brief.py --node-id A2 --peer-node A1 --json

Then do the read-only old A2 repo inventory from docs\a2_migration_context.md.
Do not port modules yet. Return Keep / Cut / Port / Rebuild plus the smallest next sprint.
```

## Good A2 To A1 Message

```text
Pulled <sha>. Tree is clean. Old runtime inventory is read-only complete.
Keep / Cut / Port / Rebuild is below. Recommended next sprint is <one small slice>.
No files changed.
```

## Failure Modes

- If a node cannot resolve git state, the brief reports `available=false` and carries the
  error.
- If the tree is dirty, the brief names changed files.
- If the branch is behind, pull or explain why not before starting new work.
- If old runtime evidence conflicts with new repo doctrine, doctrine wins unless the user
  explicitly opens a migration design decision.
