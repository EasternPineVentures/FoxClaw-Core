# Public Demo Threat Model

Status: PRACTICE.
Last updated: 2026-06-19.

This threat model exists because the demo layer is where polished public wording,
fixtures, exports, and future product surfaces begin to meet untrusted attention.
It must not become a shortcut around FoxClaw's authority boundaries.

## Assets To Protect

- private engine internals;
- local databases and raw receipts;
- Apollo founder-private material;
- secrets, keys, `.env` files, and mesh secrets;
- source reliability and evidence promotion logic;
- the user's trust in what is real versus scaffolded.

## Likely Attack Surfaces

| Surface | Risk | Control |
| --- | --- | --- |
| Public card text | HTML/Markdown injection or misleading copied content | Escape public text before rendering; fixtures are validated. |
| Raw packet intake | Prompt injection or new-source poisoning becomes a public prompt | Anti-Poisoning V0 quarantines by default and blocks instruction-smuggling phrases. |
| Trust metadata sidecar | Labels leak raw source identity or look like confidence scores | Packet Trust Metadata V0 emits public-safe labels only, with no source IDs, raw text, scores, or authority. |
| Attention receipts | Popularity pretending to be truth | Attention remains `review_priority_only`. |
| Demo commands | Convenience command loads secrets or live flags | Gym manifest rejects unsafe proof-command fragments. |
| Public exports | Private hashes, private fields, or losing forecasts hidden | Existing public export tests reject private fields and preserve results. |
| Cross-repo work | CoinFox imports private FoxClaw internals | Public contract airlock only. |
| AI-generated copy | Overconfident, vague, or invented claims | Demo script must show proof commands and current status markers. |

## Pre-Demo Security Checks

Run these before any outside-facing demo:

```powershell
python tools\foxclaw_gym.py --json
python -m pytest tests\unit\test_public_contract_schemas.py tests\unit\test_public_intelligence_card_demo.py tests\unit\test_foxclaw_gym.py tests\security\test_packet_trust_metadata_v0.py -q
python tools\check_invariants.py
git diff --check
```

## Hard No

- no live order path;
- no wallet or funds command;
- no production credentials;
- no `.env` display;
- no private Apollo material;
- no raw DB demo;
- no claim that CoinFox beta status or scaffolded Planifier internals are complete.

## Human Rule

If a demo sentence sounds impressive but cannot point to a fixture, command,
receipt, schema, or status marker, rewrite it.
