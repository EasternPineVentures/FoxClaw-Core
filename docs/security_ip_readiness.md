# Security And IP Readiness

Status: working doctrine.
Last updated: 2026-06-22.

This document defines how FoxClaw, CoinFox, Planifier, Redshift, Apollo, and future
community-node work should protect users, private data, proprietary knowledge, and the
company's right to build.

It is not a substitute for legal counsel, security review, or vendor-specific compliance
work. It is the repo-owned operating posture: what we protect, how we avoid accidental
exposure, and what must be true before broader public launch.

## Core Position

Security is not a late polish pass. It is part of the product.

The product only works if users, partners, and future contributors can trust that:

- private sources stay private;
- public outputs are deliberately sanitized;
- social attention cannot become truth by popularity alone;
- live execution authority is absent unless separately granted through hard gates;
- credentials and private corpora never enter Git, public exports, screenshots, or chat;
- founder-private strategy and IP are separated from public contracts;
- every important transformation leaves a receipt that can be audited.

The security posture should be visible in the system's behavior, tests, docs, and demos.

## Assets To Protect

### Private Data

- raw Discord or private-source content;
- private source IDs, guild/channel/message IDs, URLs, and identity hints;
- candidate lineage, receipt IDs, evidence hashes, and raw parser artifacts;
- private replay corpora and local databases;
- Apollo founder-private node messages and mesh secrets;
- trusted contributor/submission metadata before publication approval.

### Credentials And Infrastructure

- Discord credentials and future bot tokens;
- API keys, webhooks, exchange credentials, and model-provider secrets;
- GitHub tokens, deployment keys, cloud credentials, and domain/DNS access;
- local `.env` files and secret files;
- private exchange folders used by Apollo Mesh.

### Intellectual Property

- receipt-ledger design and learning-loop mechanics;
- private source-quality and setup-quality history;
- private replay datasets and labeled rejection examples;
- parser migration evidence and compatibility reports;
- scoring, readiness, promotion, quarantine, and publication policy details that are not
  explicitly approved for public release;
- product strategy, launch plans, investor/family demo scripts, and internal roadmaps;
- internal prompts, agent instructions, and protected node orchestration workflows.

### Brand And Trust

- public claims about capability, performance, or safety;
- screenshots, demo exports, and public pages;
- CoinFox social moderation and attention handling;
- any statement that could be read as trade advice, guaranteed performance, or live
  execution readiness.

## Existing Controls

FoxClaw Core already has several security-oriented controls that should remain load-bearing:

- **Paper-only authority.** Live execution and funds movement remain blocked by default.
- **Public contract airlock.** CoinFox and public nodes consume only versioned public
  contracts and explicitly exported artifacts.
- **Private/public separation.** Internal lineage can exist for audit, but public exports
  cannot expose raw private source details.
- **Publication gates.** Public cards must pass schema, semantic, and privacy validation.
- **Attention boundary.** CoinFox engagement can prioritize review but cannot become truth.
- **Fixture hygiene.** Private parser fixtures and private replay corpora stay outside Git.
- **Credential hygiene.** Secret values are not printed, committed, pasted, or logged.
- **Apollo Mesh authority locks.** Founder-node messages cannot grant order, funds,
  probability, publication, or remote-command authority.
- **Courier branch safety.** Courier can fetch, switch, track, and fast-forward; it does not
  push, reset, rebase, overwrite dirty trees, or grant authority.
- **Receipt discipline.** Decisions, parser attempts, exports, outcomes, and learning records
  are audit-shaped rather than silent side effects.

## Main Threats

| Threat | Risk | Required posture |
| --- | --- | --- |
| Private-source leakage | Raw or identifying private content reaches public JSON, screenshots, logs, or docs | Sanitize at export boundaries; test for private patterns; keep private corpora out of Git |
| Credential exposure | Tokens or secrets appear in code, chat, CLI output, fixtures, or shell history | Inspect shape, not value; use local secret files/env; rotate on suspicion |
| IP over-disclosure | Public docs reveal protected thresholds, datasets, source histories, prompts, or strategy | Public docs explain principles; protected details stay private or attorney-reviewed |
| Prompt/content injection | Untrusted text manipulates rendering, summaries, or downstream tooling | Escape public text; validate fields; never let raw content become authority |
| Data poisoning | Bad, coordinated, or private evidence enters the decision path | Quarantine first; require promotion receipts; preserve rejection reasons |
| Popularity-as-truth | Votes, comments, or saves become evidence or source reliability | Attention is review priority only; hype quarantine when heat outruns evidence |
| Branch confusion | A1/A2 work on wrong branches or overwrite each other | Courier lane manifests, clean-tree checks, no automatic push/reset/rebase |
| Community-node escape | Future public nodes gain private context or authority | Public/community nodes get scoped public-safe tasks only |
| Public claim inflation | Demos imply live trading, guaranteed performance, or investment advice | Paper labels, risk language, no individualized advice, proof commands |
| Supply-chain drift | Dependencies, connectors, or generated artifacts become unreviewed trust paths | Pin intent, review diffs, run tests/invariants, keep generated artifacts ignored unless deliberate |

## IP Protection Rules

1. Public contracts are shareable; private ledgers are not.
2. Public cards can show proof markers; they cannot show private lineage.
3. Private replay corpora, raw messages, and source histories stay local/private.
4. Proprietary thresholds, weights, and policy internals should not be published unless there
   is a deliberate release decision.
5. Screenshots and demos must be reviewed as public artifacts, not casual local views.
6. Strategy docs and launch notes should be treated as company-confidential until intentionally
   converted into public copy.
7. External contractors, agents, or future node operators should receive the smallest context
   needed for their task.
8. When in doubt, publish the outcome and method category, not the protected mechanism.

## Public Presentation Standard

A public-facing artifact may show:

- product names and purpose;
- high-level receipt-backed method;
- public contract versions;
- paper-only labels;
- evidence/readiness/risk categories;
- public-safe timestamps and outcome states;
- sanitized aggregate attention;
- public-safe learning summaries.

It must not show:

- raw Discord/private source content;
- private source identifiers or URLs;
- private receipt IDs or evidence hashes;
- internal database paths;
- credentials, token fragments, or webhook hints;
- private replay corpus paths;
- exact proprietary scoring thresholds unless approved;
- live execution claims;
- individualized trade instructions;
- unreviewed performance claims.

## Launch Readiness Checklist

Before an outside-facing launch, demo, partner review, or broader user test:

- `python -m pytest -q -rs` passes on the launch branch.
- `python tools\check_invariants.py` passes.
- `git diff --check` is clean.
- Worktree is clean or dirty files are explicitly documented and outside the public path.
- Public export validators pass.
- Public cards contain no private lineage or raw source content.
- Demo copy avoids investment-advice, guaranteed-performance, or live-execution language.
- Screenshots are reviewed for local paths, private IDs, raw logs, and private channels.
- DNS/hosting/TLS are correct for any live public page.
- Secrets are not required for public demo commands.
- A rollback path exists for public pages or exports.
- Any external repository or contractor handoff uses contracts, not private implementation.

## Security Proof Package

When asked "did you build this with security in mind?", the honest proof package is:

- project boundaries doc;
- public demo threat model;
- founder node security doc;
- Discord auth cutover and private fixture policies;
- receipt intelligence thesis;
- public contract schemas and validators;
- leakage/privacy tests;
- Courier branch-safety behavior;
- invariants output;
- full test output;
- clear paper-only/live-authority locks.

This is stronger than a claim. It shows that safety and IP boundaries are encoded in the
process.

## Near-Term Security Work

1. Keep parser migration offline and private-corpus-based until reviewed.
2. Add a reusable public-export leakage scan command that can run before every demo.
3. Create a short "public artifact review" checklist for screenshots, cards, and site copy.
4. Confirm which repos are public vs private and document what each may expose.
5. Prepare a contractor/agent context packet that excludes private data and protected IP.
6. Review domain, GitHub, email, and deployment access before launch traffic increases.
7. Decide what IP needs formal legal protection, trade-secret controls, or trademark review.

The goal is simple:

```text
Move fast, but only through guarded contracts, clean receipts, and reviewed public surfaces.
```
