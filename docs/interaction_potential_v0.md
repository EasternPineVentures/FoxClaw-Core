# Interaction Potential V0

Status: EXISTS.
Last updated: 2026-07-01.

## Purpose

Interaction Potential V0 ranks public-safe packet observations by how likely they are to
create useful CoinFox interaction:

```text
comments
challenges
saves
follow-up theses
outcome-review returns
```

It does not measure truth, evidence quality, source reliability, tradeability, or confidence.

## Command

Score the current manual packet intake fixture:

```powershell
python tools\interaction_potential.py --fixture
python tools\interaction_potential.py --fixture --json
```

Score another intake worksheet:

```powershell
python tools\interaction_potential.py --intake path\to\packet_intake.json
```

## Drivers

The V0 score is 0-100.

| Driver | Weight | Meaning |
| --- | ---: | --- |
| `clear_public_prompt` | 18 | There is a clear question users can answer or challenge. |
| `counterpoint_or_disagreement` | 15 | The item includes a natural disagreement surface. |
| `social_attention_or_native_conversation` | 14 | The item comes from, or can feed, public conversation. |
| `timely_change_or_delta` | 13 | Something changed recently enough to create urgency. |
| `money_or_position_relevance` | 12 | The item touches a market, asset, event, risk, or position question. |
| `uncertainty_or_open_question` | 10 | The item has unresolved uncertainty users can reason through. |
| `source_diversity_context` | 9 | There is enough public corroboration context to discuss responsibly. |
| `outcome_reviewable` | 9 | The item can be checked later against an outcome question. |

## Bands

| Label | Score | Meaning |
| --- | ---: | --- |
| `low_interaction_potential` | 0-39 | Too quiet or unclear without more framing. |
| `watch_interaction_potential` | 40-59 | Worth watching, but needs a stronger prompt or context. |
| `discussion_candidate` | 60-79 | Good CoinFox discussion candidate after safety review. |
| `high_reaction_potential` | 80-100 | Likely to produce comments, challenges, saves, or thesis debate. |

## What Makes Users React

For CoinFox, the strongest public prompts tend to have:

- a simple question people can answer;
- a real counterpoint;
- uncertainty rather than a finished verdict;
- a visible market/asset/event people care about;
- a recent change or delta;
- public conversation already forming;
- enough corroboration to discuss without becoming reckless;
- a later review question.

The target is useful reaction, not outrage. FoxClaw should prefer prompts that make users
reason, challenge, explain, save, or return for outcome review.

## Current Fixture Readback

The manual packet fixture currently ranks:

```text
WEN social spark -> high_reaction_potential
Prediction-market odds shift -> high_reaction_potential
BTC invalidation delta -> high_reaction_potential
```

WEN ranks highest because it has social/native attention, a direct question, an obvious
counterpoint, and a later outcome-review question.

## Boundary

Interaction potential can:

- rank which packet observations to draft first;
- suggest why users may comment or challenge;
- help CoinFox ask better thesis prompts;
- create a better outcome-review queue.

Interaction potential cannot:

- prove a claim true;
- promote evidence;
- change source reliability;
- publish to CoinFox;
- train a model;
- authorize trading or funds movement.

## Hard Rails

```text
can_submit_order = false
can_move_funds = false
live_execution_allowed = false
can_publish_to_coinfox = false
can_change_truth = false
can_promote_evidence = false
can_change_source_reliability = false
can_update_verified_memory = false
can_train_model = false
```
