# ADR: A Signal Is Not A Trade

Status: Accepted.
Date: 2026-06-19.

## Context

A trader can correctly predict direction and still lose by entering late,
oversizing, using too much leverage, ignoring liquidity, chasing after the move,
or taking poor reward-to-risk terms.

## Decision

FoxClaw may describe signal confidence, but it may not present a signal as a
trade until a Trade Readiness Verdict exists. Readiness must distinguish evidence
quality, edge, tradeability, risk, entry quality, and plan readiness.

## Consequences

- Public cards must be able to say "good thesis, bad trade right now."
- High-risk opportunities must be classified honestly as Tactical, Speculative,
  Redline, or Reject.
- Planifier owns the user's plan and practice layer; FoxClaw Core owns evidence,
  edge, readiness, and paper-only verdicts.
