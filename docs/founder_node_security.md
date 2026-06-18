# Founder Node Security

Apollo nodes are founder nodes.

That makes them powerful and dangerous in a different way from public/community nodes. They
may hold private strategy, migration context, runtime truth, architecture decisions, and IP
that should not be copied into public artifacts by accident.

## Doctrine

Founder nodes can coordinate private work.

Founder nodes cannot accidentally make that work public.

The default posture is:

```text
node_role=founder_node
data_classification=founder_private
redistribution=do_not_export
public_export_allowed=false
```

This is now encoded in Apollo Mesh V0 events.

## Why

FoxClaw's value is not only code. It is:

- decision doctrine;
- receipts and track record;
- migration judgment;
- private runtime knowledge;
- source/evidence handling;
- node workflow;
- founder operating taste.

That is IP. Treat it as protected until deliberately distilled into a public-safe contract or
product surface.

## What Founder Nodes May Share

Inside the founder mesh, A1 and A2 may share:

- repo truth;
- handoff notes;
- runtime observations;
- private planning context;
- research questions and answers;
- paper-only receipts;
- Redshift/FoxClaw boundary receipts;
- migration inventory.

## What Founder Mesh Events May Not Carry

Apollo Mesh V0 rejects content fields that look like:

- commands;
- live order IDs;
- account IDs;
- funds movement;
- authority flags;
- API keys;
- passwords;
- tokens;
- private keys;
- secrets.

The mesh can share context. It cannot carry remote-control power.

## Public/Community Nodes Are Later

Do not connect public/community nodes to the founder mesh.

Future public nodes need a separate contract:

- sanitized payloads only;
- no founder-private classification;
- no old runtime paths;
- no private strategy notes;
- no secret-bearing metadata;
- no authority.

Until that exists, Apollo Mesh is founder-only.

## Speed Advantage

The point is to move faster without leaking the crown jewels:

1. Founder nodes exchange signed local events quickly.
2. A1/A2 converge on current truth.
3. Useful public-safe artifacts are deliberately exported later.
4. Private strategy and migration context stay in founder space.

That is how FoxClaw gets quicker and safer at the same time.
