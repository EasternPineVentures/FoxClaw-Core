# CoinFox Discord Representative Bot Design

Owner: CoinFox founder/operator.
Date: 2026-06-25.
Status: design checkpoint.

## Purpose

The CoinFox Discord bot should act as a company representative when the founder
is not present. For launch, it responds only when mentioned. It is not a trading
assistant, signal bot, parser bot, moderation bot, or private-history interface.

The bot should make the public server feel staffed without giving the bot broad
authority. It explains CoinFox, routes people to the right public channel,
repeats risk boundaries, and escalates founder-only questions.

## Selected Approach

Use the hybrid representative approach:

1. Deterministic representative core first.
2. Optional LLM wording layer later.
3. Mention-only behavior for launch.

The first implementation should be dependency-light and use Discord REST polling
against a public-channel allowlist. A gateway client can be added later if the
server needs lower latency or richer events.

## Public Scope

The bot may answer mentions in these public categories only:

- `START HERE`
- `COINFOX`
- `FOXCLAW IDEAS`
- `LEARN`
- `SUPPORT`

The bot must ignore or refuse to operate in:

- `FOUNDER VAULT`
- `RESET STAGING`
- legacy private categories
- archived/server-history channels
- bot logs, parser logs, raw feeds, or old signal channels
- direct messages, unless a future design explicitly enables them

## Capabilities

When mentioned, the bot can:

- welcome new users;
- explain what CoinFox is;
- explain the public channel layout;
- explain rules and risk boundaries;
- explain that signals are ideas, not trade instructions;
- explain what FoxClaw public intelligence means;
- route people to `trade-ideas`, `questions`, `help`, or `reports`;
- say when the founder is needed;
- provide short launch-safe copy for public onboarding.

## Refusals

The bot must refuse or redirect requests to:

- give financial advice;
- say whether to buy, sell, enter, exit, hold, size, or leverage a trade;
- promise returns or imply guaranteed profit;
- impersonate the founder;
- expose private archive, Founder Vault, Reset Staging, bot-log, parser-log, or
  legacy-channel details;
- summarize raw private Discord history;
- reveal credentials, tokens, invite internals, server IDs, channel IDs, or
  user IDs;
- claim FoxClaw has placed or will place trades;
- treat public intelligence as personalized advice.

Refusals should be short, calm, and useful. Example:

```text
I cannot tell you what to trade. I can help frame the idea, risk, invalidation,
and where to discuss it. For setups, use #trade-ideas and label uncertainty
clearly.
```

## Tone

The bot should sound like a calm front-desk representative for CoinFox:

- clear;
- warm;
- concise;
- confident about boundaries;
- not sterile;
- not hype-driven;
- never pretending to be the founder.

Default identity line:

```text
I am the CoinFox bot. I can explain the server, route questions, and keep the
risk line clear. I cannot give financial advice or tell anyone what to trade.
```

## Knowledge Pack

The initial deterministic knowledge pack should include:

- welcome copy;
- rules summary;
- risk disclaimer;
- signals-are-not-trades explanation;
- channel guide;
- FoxClaw public intelligence explanation;
- founder escalation language;
- supported command/mention examples;
- refusal templates.

The knowledge pack should live in repo-tracked configuration or code fixtures.
It must not include private archive content, raw signal calls, private message
quotes, Discord IDs, credentials, or unredacted screenshots.

## Runtime Architecture

Components:

- `RepresentativePolicy`: classifies an incoming mention as answerable,
  route-only, refusal, or ignore.
- `RepresentativeKnowledge`: returns approved public-safe answer snippets.
- `DiscordMentionPoller`: reads recent messages from allowed public channels
  through Discord REST.
- `DiscordReplyClient`: posts a reply to the triggering public channel.
- `StateStore`: records the last processed message per channel in a local file
  outside git or under an ignored runtime path.

Data flow:

1. Load bot token from `COINFOX_DISCORD_BOT_TOKEN`.
2. Load allowed channel IDs from a config file or generated snapshot mapping.
3. Poll allowed public channels.
4. Keep only messages that mention the bot and were not sent by the bot.
5. Classify the request.
6. Produce deterministic reply text.
7. Post the reply.
8. Update last-seen state.

No event should read local archive exports or private Discord history.

## Mention Rules

The bot replies only when:

- the message is in an allowed public channel;
- the message mentions the CoinFox bot user;
- the message is not authored by a bot;
- the message ID is newer than the channel's last processed message.

The bot ignores:

- messages without mentions;
- messages in disallowed channels;
- bot-authored messages;
- messages that appear older than the current processed cursor.

## LLM Layer

The launch version should not require an LLM. If an LLM is added later, it must:

- receive only public-safe knowledge snippets;
- receive the user's current mention text;
- never receive archive exports or private Discord history;
- be wrapped by the same refusal policy before and after generation;
- keep deterministic fallbacks when the model is unavailable;
- log only public-safe metadata, not raw private content.

## Operations

The bot should start in dry-run mode first:

```text
read mentions -> classify -> print intended reply -> do not send
```

Live mode should require an explicit flag:

```text
--send
```

Operational logs should include:

- timestamp;
- channel name or configured public label;
- message hash or message ID for dedupe;
- classification;
- whether a reply was sent.

Logs must not include credentials or private archive material.

## Testing

Unit tests should cover:

- mention-only gating;
- public-channel allowlist;
- private-channel ignore behavior;
- financial-advice refusal;
- archive/private-history refusal;
- channel routing responses;
- welcome/help responses;
- state cursor dedupe;
- dry-run behavior;
- send mode requiring explicit `--send`.

Integration-safe tests should use fake Discord clients. Live Discord tests should
remain manual and opt-in.

## Acceptance Criteria

- The bot does not answer unmentioned messages.
- The bot answers mentions only in the configured public channel allowlist.
- The bot refuses direct trade advice and private-history requests.
- The bot can explain CoinFox, FoxClaw public intelligence, rules, risk, and
  channel routing.
- The bot can run in dry-run mode without sending messages.
- Live sending requires an explicit flag.
- No private archive files are read by the bot.
- No tokens or secrets are printed.
- Tests pass before live use.

## Non-Goals

- No trade execution.
- No signal parsing.
- No live market analysis.
- No public invite creation.
- No moderation automation.
- No private archive search.
- No founder impersonation.
- No proactive conversation starter.
