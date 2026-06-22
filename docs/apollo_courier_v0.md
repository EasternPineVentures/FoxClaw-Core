# Apollo Courier V0

Apollo Courier is the operator-facing wrapper around Apollo node coordination.

V0 has two jobs:

- keep A1/A2 on the expected Git branch without paste-heavy PowerShell handoffs;
- let each node resolve its expected branch from a shared lane manifest;
- send signed founder-private mesh events when a node needs to ask, answer, alert, or
  leave a receipt.

Courier does not push, reset, rebase, publish, connect Discord, move funds, submit orders,
or grant remote command authority.

## Branch Sync

Inspect the current repo against an expected branch:

```powershell
python tools\apollo_courier.py branch-sync `
  --target-branch feature/parser-compat-v0 `
  --fetch `
  --json
```

Apply the safe plan:

```powershell
python tools\apollo_courier.py branch-sync `
  --target-branch feature/parser-compat-v0 `
  --apply `
  --json
```

`--apply` may run only these safe operations:

- `git fetch --prune <remote>`;
- `git switch <branch>`;
- `git switch -c <branch> --track <remote>/<branch>`;
- `git branch --set-upstream-to <remote>/<branch> <branch>`;
- `git pull --ff-only`.

It refuses to act when:

- the worktree is dirty;
- the target branch does not exist locally or on the remote;
- the current branch has diverged from upstream;
- the branch is ahead and needs a human-approved push.

## Lane Sync

The shared lane map lives at:

```text
config/apollo_courier_lanes.json
```

List known lanes:

```powershell
python tools\apollo_courier.py lanes --json
```

Ask where one node should be for a lane:

```powershell
python tools\apollo_courier.py lane-sync `
  --node-id A2 `
  --lane parser-compat-v0 `
  --fetch `
  --json
```

Apply the safe branch move:

```powershell
python tools\apollo_courier.py lane-sync `
  --node-id A2 `
  --lane parser-compat-v0 `
  --apply `
  --json
```

This resolves `A2 + parser-compat-v0` to the manifest's target branch, then uses the same
safe branch-sync rules above. The manifest is intentionally small and explicit so the
project can change lane ownership without rewriting commands in chat.

## Signed Courier Messages

Courier delegates existing Apollo Mesh commands, so these remain valid:

```powershell
python tools\apollo_courier.py --node-id A1 --json heartbeat --message "A1 online"
python tools\apollo_courier.py --node-id A1 --json sync
```

New useful message verbs:

```powershell
python tools\apollo_courier.py --node-id A1 --json manifest `
  --capability branch-sync `
  --status available

python tools\apollo_courier.py --node-id A1 --json ask `
  --to-node A2 `
  --question "Which branch should A2 validate?" `
  --priority high

python tools\apollo_courier.py --node-id A2 --json answer `
  --to-node A1 `
  --question-event-id sha256:<question-event-id> `
  --answer "A2 is on feature/parser-compat-v0"

python tools\apollo_courier.py --node-id A2 --json alert `
  --severity warning `
  --message "Worktree is dirty" `
  --source branch-sync

python tools\apollo_courier.py --node-id A2 --json receipt `
  --title "A2 branch aligned" `
  --summary "feature branch tracks origin and the tree is clean" `
  --status ready
```

All mesh events stay founder-private:

```text
data_classification=founder_private
redistribution=do_not_export
public_export_allowed=false
can_remote_command=false
```

The content scanner rejects forbidden fields and obvious credential-like values before an
event is signed or written.
