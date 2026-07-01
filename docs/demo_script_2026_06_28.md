# June 28, 2026 Showing Notes

Status: OPTIONAL NOTES.
Last updated: 2026-06-19.

These notes are optional. The primary first-encounter surface is
`docs/first_encounter_guide.md` or `python tools\foxclaw_visitor_guide.py`.
Do not treat this as a pitch script.

Demo order:

```text
FoxClaw -> CoinFox -> Planifier
```

## Opening Idea

FoxClaw is not trying to be a magic trade button. It is trying to help people
avoid turning good information into bad trades.

The demo is paper-only. Nothing here can place a live order or move funds.

## Open First

Open:

```powershell
python tools\foxclaw_visitor_guide.py
```

## FoxClaw Map

Open:

```powershell
python tools\foxclaw_gym.py
```

Say:

```text
This is the gym. It tells us what is ready, what needs practice, and what gets
attention next before anything becomes public-facing.
```

## FoxClaw Public Airlock

Open:

```powershell
python -m pytest tests\unit\test_public_contract_schemas.py -q
```

Say:

```text
Public products do not reach into FoxClaw's private brain. They consume versioned
public contracts.
```

## FoxClaw Doctor

Open:

```powershell
python tools\forecast_desk_doctor.py --fixture --json
```

Say:

```text
FoxClaw can explain why it is quiet. Silence is allowed. Making up a trade is not.
```

## FoxClaw Public Hunt Export

Open:

```powershell
python tools\forecast_desk_export_public.py --fixture --write data\demo_export --json
```

Say:

```text
Public exports are paper-labeled and sanitized. Losing or resolved forecasts stay
visible because learning needs the full record.
```

## FoxClaw Boundary and Learning

Open:

```powershell
python tools\redshift_paper_boundary.py --fixture --json
python tools\forecast_learning_spine.py --fixture --json
```

Say:

```text
Information can travel to a paper lab. Authority cannot. Then paper outcomes
come back as learning receipts.
```

## CoinFox Card

Open:

```powershell
python tools\public_intelligence_card_demo.py --fixture
```

Say:

```text
CoinFox is now live in rough beta at `https://coinfox.foxclaw.cloud/`. It shows the
public social shape: markets, predictions, theses, discussions, account gates,
standards, and receipt-style context. It is close to a controlled real-user test, but it is
still beta, not production launch. FoxClaw intelligence can appear inside that social flow
as context: the claim, the evidence, the attention, the risk, and what a professional would
wait for.
```

Point out:

- CoinFox should feel like a familiar social feed, not a rigid workflow;
- traders can talk about anything trading-related;
- upvotes and comments help discovery but do not become truth;
- attention is shown, but it does not become truth;
- the risk can be exciting without being beginner-safe;
- the card can say "good thesis, bad trade right now."

## Planifier

Say:

```text
Planifier is already built, but it needs work. In this ecosystem it becomes the
practice layer: FoxClaw structures the information, CoinFox presents it publicly,
and Planifier helps the user build a plan, invalidation, sizing discipline, and
a journal.
```

Do not imply Planifier is fully wired into this flow yet. Say the product exists,
and the next work is tightening the connection.

## Close

Say:

```text
The direction is a professional intelligence fabric: attention, evidence, risk,
tradeability, and practice stay separate. The goal is not more signals. The goal
is better decisions.
```

## Do Not Show

- secrets, keys, local DBs, or private Apollo material;
- live execution language;
- raw internal engine details unless someone asks;
- private or unstable CoinFox internals;
- too many JSON receipts in a row.
