# Apollo Mesh V0 Design

## Status

Draft for A1/A2 review. This spec defines the first usable FoxClaw node-network slice:
private, signed, near-real-time network intel between Apollo workstations.

This is not cutover work. This does not grant execution authority. This does not share node
databases. It creates a shared event substrate so Apollo nodes can see, verify, and retain
each other's context at a moment's notice.

## Current Coordination Truth

- A1 and A2 are meant to work from the same `foxclaw-core` GitHub repo.
- A2 now has a real clone at `C:\Users\fox1i\Desktop\FoxClaw-Core`.
- Remote `origin/master` is still at `0.1.4` as of this draft.
- A1's reported `0.4.3` / "ahead 15" work is not visible on GitHub yet.
- Implementation should not begin until A1 either pushes the `0.4.3+` baseline or confirms
  that this spec branch should be rebased after those commits land.

## Goal

Make Apollo 1 and Apollo 2 act like a real collective by exchanging signed, structured
network-intel events through a private relay. Each node should be able to answer:

- Which Apollo nodes are alive?
- What repo version and capability set is each node running?
- What did another node just observe?
- What needs attention right now?
- What handoff or question did another node leave?
- Which facts were received, verified, and stored locally?

The network also needs a small adaptive intelligence that lives beside the event log: a
local **Mesh Steward** on each node. The steward watches verified network intel, keeps track
of open questions, handoffs, alerts, stale work, and repeated patterns, then emits its own
signed summaries and reminders back into the mesh.

The larger direction is an **agent workbench**: a place where different AI sources,
workstations, tools, and future agents can build together without losing context. FoxClaw
should feel like one continuous advanced collaborator with excellent memory, but internally it
must preserve provenance: which node, model, tool, source, or human produced each piece of
context. The shared memory is the signed event log plus derived context packs, not an
unattributed blob of chat history.

The public-facing path is a downloadable **Node Test Package**. It lets trusted testers run a
safe, limited test node that can join a sandbox relay, publish signed test intel, receive
steward digests, and produce diagnostics without getting access to private FoxClaw internals,
live runtime state, or decision authority.

## Non-Goals

- No live orders, funds movement, custody, or account authority.
- No remote execution.
- No remote probability setting.
- No shared SQLite database.
- No OneDrive-synced source of truth.
- No public relay, public feed, or secret-bearing event content.
- No solicitation, purchase, acceptance, or use of confidential market-moving information.
- No insider-source workflow, private tip workflow, or MNPI-bearing network-intel workflow.
- No Forecast Desk decision influence in V0.
- No autonomous manager authority. The steward can notice, summarize, remind, and propose;
  it cannot command, execute, mutate decision state, or bypass local policy.
- No pretending multiple AI sources are one untraceable model. The user experience can feel
  continuous, but every memory and recommendation must retain source provenance.
- No downloadable package that contains private DBs, runtime logs, secrets, A1/A2 private
  keys, private thresholds, live adapters, or internal-only strategy code.

## Approach

Use a private Nostr-style relay as the first transport, while FoxClaw owns the internal
network-intel schema.

Nostr is a good fit because its base object is already a signed event with a public key,
timestamp, kind, tags, content, id, and signature. NIP-01 defines that event and WebSocket
relay flow. NIP-42 defines relay authentication through a signed challenge event. FoxClaw
should use those protocol shapes, but keep FoxClaw authority rules outside the relay.

Recommended relay implementation for V0: `nostr-rs-relay` or another mature private relay
with whitelisted pubkeys and NIP-42 support. Do not write a relay from scratch in V0.

## Architecture

FoxClaw splits network identity, event schema, local persistence, steward memory, and
transport:

```text
foxclaw/node/
  identity.py      # node id, local private key path, public key, capability descriptor
  events.py        # FoxClaw NodeEvent schema, canonical serialization, validation
  store.py         # local append-only inbox/outbox JSONL or SQLite log
  steward.py       # adaptive local manager over verified mesh events
  context.py       # context pack builder for handoffs, agents, and work sessions
  cli.py           # heartbeat, handoff, alert, inbox, sync commands

foxclaw/adapters/nostr/
  mapping.py       # FoxClaw NodeEvent <-> Nostr event kind/tags/content
  client.py        # publish/subscribe to a private relay

foxclaw/adapters/agents/
  __init__.py      # future source adapters for external/local AI assistants

foxclaw/testkit/
  package.py       # safe node-test package metadata and capability limits
  diagnostics.py   # local environment, relay, identity, and schema checks
  fixtures.py      # fake/synthetic test intel, never private production data
```

`foxclaw/node` owns the domain model. `foxclaw/adapters/nostr` owns relay mechanics. The
engine does not import the adapter, and the relay never becomes an authority layer.

## Mesh Steward

The Mesh Steward is FoxClaw's little network manager. It is an adaptive intelligence that
tracks the node network's working memory without owning the work.

In V0 it should be deliberately simple and deterministic:

- read verified inbox/outbox events;
- maintain a local state snapshot of nodes, open questions, active handoffs, alerts, and
  unresolved intel;
- detect stale handoffs, unanswered questions, repeated alerts, missing heartbeats, and
  dirty repo states;
- emit signed `steward.digest`, `steward.reminder`, and `steward.escalation` events;
- explain every reminder with event ids it is based on.

The steward is adaptive through memory first, not model magic. It learns from the event log:
what each node tends to know, which alerts recur, which questions remain open, and where work
gets stuck. Later versions may add local LLM summarization, but V0 must work without network
LLM calls and without new heavy dependencies.

The steward is advisory-only. It never executes a task, never changes probabilities, never
writes into GroveCore decision tables, and never treats its own summaries as facts unless they
cite accepted source events.

## Agent Workbench And Shared Memory

Apollo Mesh is the substrate where agents can build. V0 should not try to integrate every AI
source, but it must lay the rails for that future.

The workbench has three jobs:

- **Capture:** every meaningful interaction becomes a signed event or local receipt with
  source provenance.
- **Remember:** the Mesh Steward turns verified events into compact, cited context packs.
- **Route:** future adapters can hand the right context pack to ChatGPT, Claude, local models,
  Codex, Redshift, or a domain-specific worker without losing the thread.

Context packs are derived artifacts, not raw authority. A context pack should include:

- purpose of the current work;
- relevant accepted events and receipt ids;
- unresolved questions;
- active constraints and invariants;
- recent decisions;
- source/provenance map;
- what the receiving agent is allowed and not allowed to do.

Initial agent-oriented event types:

- `agent.session.started`: an agent/model/tool work session began.
- `agent.context_pack.created`: a cited context pack was produced for an agent.
- `agent.output.received`: an agent returned useful output.
- `agent.memory.note`: durable lesson or memory proposed from a session.
- `agent.memory.accepted`: local steward accepted a memory note into derived memory.
- `agent.memory.rejected`: local steward rejected or quarantined a memory note.

V0 implementation may store these locally only. Relay publishing can wait until identity,
roster, and base network-intel events are reliable.

## Downloadable Node Test Package

The test package is how FoxClaw starts testing a wider node network before the full organism
is ready to distribute. It should be small, boring, and aggressively safe.

The package should initially ship as a GitHub release artifact or private package, not a
public open install, until the security boundary has been proven. Testers should be able to:

- install the package in a clean Python environment;
- generate a test-only node identity;
- connect to a sandbox private relay;
- publish `node.heartbeat`, `intel.observation`, and `question.ask` test events;
- receive and verify signed events from the sandbox;
- run local diagnostics and export a redacted node report;
- inspect what the Mesh Steward thinks is stale, open, or important.

The package must not include:

- private A1/A2 node keys;
- production `grove_core.db`;
- runtime logs;
- `.env` files;
- live execution adapters;
- private scoreboard thresholds;
- old A2 legacy code.

Distribution should happen in phases:

1. **Internal wheel:** A1/A2 install from a locally built wheel and verify the CLI works.
2. **Private release artifact:** trusted testers download a wheel from a private GitHub
   release or package registry.
3. **Sandbox onboarding pack:** testers receive a relay URL, test roster entry, and clear
   instructions for generating a test identity.
4. **Public-ready testkit:** only after secret scan, package audit, and sandbox relay abuse
   testing pass.

The package is a testkit, not the product. It proves node identity, signed network intel,
relay sync, steward memory, diagnostics, and install ergonomics.

## Node Identity

Each Apollo node has:

- `node_id`: stable local name, for example `apollo-1` or `apollo-2`.
- `pubkey`: public signing key.
- `private_key`: local-only secret stored outside git.
- `capabilities`: declared read/write event kinds the node supports.
- `repo_state`: repo name, branch, commit, version, dirty flag.

Private keys are never committed and never printed. Public keys may be committed in a trusted
roster file after A1/A2 agree on the names.

## Event Model

FoxClaw NodeEvent content is canonical JSON with this shape:

```json
{
  "schema_version": 1,
  "event_type": "node.heartbeat",
  "from_node": "apollo-2",
  "created_at": "2026-06-18T00:00:00Z",
  "priority": "normal",
  "summary": "Apollo 2 is online",
  "payload": {},
  "references": [],
  "authority": {
    "can_submit_orders": false,
    "can_move_funds": false,
    "can_set_probabilities": false,
    "can_execute_remote_actions": false
  }
}
```

The Nostr wrapper supplies transport id, pubkey, relay timestamp, and signature. FoxClaw
validates both the Nostr signature and the FoxClaw payload contract before storing the event.

## V0 Event Types

- `node.heartbeat`: node alive, repo version, dirty flag, clock time.
- `node.capability_manifest`: event kinds the node can publish or consume.
- `handoff.note`: work handoff, blockers, current branch, next action.
- `runtime.alert`: warning from a node, such as stale scoreboard or failed ingest.
- `intel.observation`: context-only fact observed by a node.
- `intel.receipt`: retained evidence with source, confidence note, and local receipt id.
- `question.ask`: question from one node to the collective.
- `question.answer`: answer tied to a question event id.
- `steward.digest`: manager summary of current network state.
- `steward.reminder`: manager reminder about stale handoff, unanswered question, or missing
  heartbeat.
- `steward.escalation`: manager marks something as needing human/local-node review.
- `agent.context_pack.created`: cited memory bundle for a model/tool/agent session.
- `agent.memory.note`: proposed durable memory from a model/tool/agent session.
- `testkit.diagnostic`: redacted tester-side diagnostic report.
- `testkit.join_request`: signed request for a test node to join the sandbox roster.

V0 intentionally keeps Forecast Desk event types out until the base node mesh is reliable.

## Network Intel Rules

Network intel is context, not command.

- It can inform a local decision process.
- It can be cited by a receipt.
- It can trigger local review or local ingestion.
- It cannot execute an action.
- It cannot set final probability.
- It cannot override local policy.
- It cannot mutate the local GroveCore database directly.

Every imported intel event receives local receipt status:

- `received`: relay delivered it.
- `verified`: signature and roster check passed.
- `accepted`: payload schema and policy passed.
- `quarantined`: signature, roster, schema, clock, or policy failed.

## Market Integrity / MNPI Firewall

Apollo Mesh V0 is a signed public-intelligence and memory network. It must be designed so
FoxClaw can clearly say what it does not do: it does not buy secrets, solicit insiders, trade
on confidential information, or let node intel execute actions.

Accepted `intel.observation` and `intel.receipt` events must include source provenance and a
shareability attestation. The accepted source lane is limited to:

- `public_url`
- `official_release`
- `licensed_data`
- `own_observation`
- `analysis`

Each accepted intel payload must state:

- source type;
- evidence, such as a public URL, license note, observation note, or analysis note;
- rights attestation that the sender can share it and that it is not confidential;
- MNPI status of `not_mnpi`.

Events with missing provenance, missing attestation, `unknown` MNPI status,
`suspected_mnpi`, or `confidential_rejected` must be quarantined locally. Quarantined intel
can be logged and reviewed, but it cannot become accepted memory, feed a steward digest as
trusted fact, execute an action, set probabilities, or influence any production trading or
prediction-market path.

This firewall belongs in code, not just copy. The first implementation slice must include
tests proving accepted public intel passes and suspicious/non-public intel quarantines.

## Relay Policy

The V0 relay must be private:

- Whitelist A1 and A2 pubkeys.
- Require authenticated writes when supported.
- Reject unknown pubkeys.
- Reject future-dated events beyond a small clock-skew window.
- Limit event size.
- Preserve stored events long enough for nodes to catch up after downtime.

Public Nostr relays are out of scope for Apollo Mesh V0.

## CLI Workflow

The first usable commands should be boring and fast:

```bash
python -m foxclaw.node.cli heartbeat
python -m foxclaw.node.cli handoff "A2 has mesh design ready; blocked on A1 baseline push."
python -m foxclaw.node.cli alert --priority high "A2 old runtime DB is still active."
python -m foxclaw.node.cli inbox --limit 20
python -m foxclaw.node.cli steward digest
python -m foxclaw.node.cli steward reminders
python -m foxclaw.node.cli context pack --purpose "A1/A2 mesh implementation"
python -m foxclaw.node.cli sync
python -m foxclaw.testkit.diagnostics
```

The CLI should default to dry, local-safe behavior. Publishing requires an explicit relay URL
from config or environment.

## Error Handling

- Missing private key: fail closed and explain how to generate one.
- Unknown sender pubkey: store as quarantined, do not display as trusted intel.
- Bad signature: store as quarantined.
- Bad schema: store as quarantined with validation errors.
- Relay unavailable: keep outbound event in local outbox for retry.
- Duplicate event id: ignore duplicate body, retain first-seen metadata.
- Clock skew: warn on local clock drift; quarantine extreme future events.

## Testing

Minimum tests for the implementation plan:

- NodeEvent canonical serialization is stable.
- Event ids are deterministic.
- Signing and verification pass for the right key and fail for the wrong key.
- Authority flags default false and cannot be omitted.
- Unknown event types are rejected or quarantined.
- Public-intel events with source provenance, evidence, attestation, and `not_mnpi` status
  are accepted by the compliance firewall.
- Intel events with missing attestation, `unknown` MNPI status, `suspected_mnpi`, or
  `confidential_rejected` are quarantined.
- Local store appends inbox/outbox records without overwriting.
- Duplicate event ids do not create duplicate accepted records.
- Nostr mapping preserves event type, node id, priority, references, and content.
- CLI heartbeat produces a valid local event without contacting a relay.
- Steward digest cites source event ids and does not invent unsupported facts.
- Steward reminder fires for stale handoffs and unanswered questions.
- Steward output remains advisory-only with all authority flags false.
- Context pack includes purpose, cited events, constraints, open questions, and allowed
  actions.
- Agent memory notes require explicit local acceptance before becoming durable memory.
- Testkit diagnostics redact secrets and local paths that should not be shared.
- Testkit package excludes DB files, env files, runtime logs, and old legacy code.
- Testkit-generated node identities are test-only and cannot impersonate A1 or A2.

## A1 Alignment Packet

Message for A1:

```text
A2 is ready to make Apollo Mesh V0 the first real node-network slice.

Proposed scope:
- private Nostr-style relay transport;
- FoxClaw-owned signed network-intel schema;
- first event types: heartbeat, capability manifest, handoff note, runtime alert,
  intel observation, intel receipt, question ask/answer, steward digest/reminder/escalation;
- each node runs a local Mesh Steward: a little adaptive manager that tracks verified mesh
  events, remembers open loops, and emits signed summaries/reminders;
- Apollo Mesh is also the foundation for the agent workbench: context packs, durable memory,
  and provenance across AI sources so agents can build without losing the thread;
- a downloadable Node Test Package is the path to testing outside nodes safely: sandbox relay,
  test-only identity, signed test intel, steward diagnostics, and no private runtime payloads;
- no remote execution, no probability setting, no funds/orders, no shared DB.

A2 found that GitHub origin/master is still at 0.1.4 and does not include the reported
0.4.3 / A2 migration context commit. Please push A1's baseline or tell A2 which branch to
base Apollo Mesh V0 on. A2 will keep implementation on a separate branch until the baseline
is visible.
```

## References

- Nostr NIP-01: signed event format and relay WebSocket flow.
  <https://github.com/nostr-protocol/nips/blob/master/01.md>
- Nostr NIP-42: client authentication to relays through signed challenge events.
  <https://github.com/nostr-protocol/nips/blob/master/42.md>
- Nostr NIP-11: relay information document and relay limits.
  <https://github.com/nostr-protocol/nips/blob/master/11.md>
- `nostr-rs-relay`: mature relay implementation with SQLite persistence and NIP support.
  <https://github.com/scsibug/nostr-rs-relay>
