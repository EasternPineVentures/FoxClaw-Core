# Project Boundaries

Status: EXISTS as architecture doctrine.
Last updated: 2026-06-19.

## Coordination Rule

GitHub is the coordination layer. Each repository owns one system. Contracts cross
repository boundaries; implementation details do not.

## Repository Ownership

| Repository or system | Owns | Must not own |
| --- | --- | --- |
| `foxclaw-core` | Claims, evidence quality, edge, readiness, gates, public contracts | CoinFox posts, engagement persistence, Planifier journals, Redshift experiments |
| `CoinFox` | Public posts, comments, branching replies, votes, engagement events, public feeds, social discussion, public cards, idea-following and spotlight surfaces | FoxClaw private engine, Grove receipts, Apollo private data |
| `Planifier` | User plans, checklists, journals, execution discipline | FoxClaw scoring authority, public feed ranking |
| `redshift_core` | Experimental research, paper probes, protected lab workflows | FoxClaw decision authority or public truth |
| The Grove | Receipts, lineage, promoted evidence, outcomes | Public social engagement or popularity scoring |
| Apollo | Founder-private intelligence, strategy research, protected coordination | Public export by default |
| Future FoxClaw Node | Contribution tasks, validation checks, node reputation | Capital authority, trade approval, source-trust mutation |
| EasternPineVentures GitHub | Organization registry, issues, dependencies, project board | Runtime ownership |

## Contract Boundary

CoinFox and public nodes may consume only versioned public contracts from
`foxclaw/contract/public/` or exported artifacts explicitly marked public.

Forbidden coupling:

- no FoxClaw database access from CoinFox;
- no import of `foxclaw.engine` from CoinFox;
- no access to Apollo private data;
- no mutation of Grove receipts;
- no use of CoinFox popularity as evidence truth.

## GitHub Project Fields

Use one organization-wide GitHub Project with fields like:

```text
Owning Repo
System
Status
Phase
Dependency
Public/Private
Contract Version
Launch Critical
```

Suggested labels:

```text
system:foxclaw-core
system:coinfox
system:planifier
system:node-network
type:contract
type:foundation
type:integration
status:deferred
status:blocked
boundary:public
boundary:private
```

Issues stay in the repository that owns the work. Cross-repo dependencies should
link to issues instead of duplicating task lists.

## Current Build Rule

When FoxClaw Core encounters a CoinFox dependency:

1. Define the public contract.
2. Write a fixture.
3. Document the missing CoinFox framework.
4. Reference the owning issue.
5. Stop at the repository boundary.

The fractured look is intentional sequencing, not architectural confusion.
