"""Market scoreboard builder — the market-and-store half of the v1 scoreboard.

This is the customs house at the engine border. On the *market* side it speaks symbol,
side, entry/exit price, PnL, source_id, and it carries the corruption filters that encode
invariant #8 ("a mis-parsed price must never fake a track record"). On the *engine* side it
hands across only neutral terms — a subject id, a success rate, a reward factor, a sample
size, neutral observations — and lets ``engine.score`` / ``engine.edge`` / ``engine.gate``
do the deciding. No decision math lives here; no market vocabulary leaks into ``engine/``
(invariant #4).

The full chain this enables, end to end:

    store paper outcomes
      → adapter builds neutral observations + per-subject aggregates (corruption-filtered)
      → engine.edge estimates the edge (posterior P(EV>0), commitment)
      → engine.score grades the subject onto a tier
      → engine.gate applies the tier's commitment multiplier
      → receipt-compatible verdict (``assess_setup``)

DB access is delegated to ``store`` (``PaperOutcomeStore.get_closed_outcomes_with_source``),
never a hardcoded path (resolves the spirit of P5). Read-only: this builds a scoreboard, it
never writes the DB, never places orders, never moves funds (invariant #1).

Ported from v1 ``tools/setup_performance_summary.py`` — its ``build_scoreboard`` /
``_return_fraction`` / corruption-filter half; the scoring math went to ``engine/score.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from statistics import median
from typing import Any, Iterable, Mapping

from ...engine import gate, score
from ...engine.edge import BayesianEdge, EdgeVerdict, Observation
from ...store.outcomes import PaperOutcomeStore
from .setup import setup_key

# ── Corruption filters — invariant #8 in code ──────────────────────────────────
# A single paper trade cannot plausibly return more than this; beyond it the entry/exit
# price is almost certainly corrupt, so the row is dropped (one bad row can't fake a setup).
RETURN_SANITY_CAP = 1.0                  # 100% single-trade return
# An entry that sits far from the symbol's median entry is almost certainly mis-parsed
# (an asset can't be two very different prices at once). The median is robust, so a
# minority of corrupt rows can't move the reference they are checked against.
ENTRY_OUTLIER_RATIO = 2.0                # entry > 2x or < 0.5x the symbol median
MIN_SYMBOL_TRADES_FOR_ENTRY_CHECK = 4    # entries needed for a trustworthy median

# Sources that must never appear in the scoreboard: price/context feeds (never trade
# signals) and test/synthetic sources, so contaminated history can't skew the gate.
EXCLUDED_SOURCE_IDS = {
    "kraken_public_ticker",
    "redshift_market_stream",
    "redshift_kraken_info_stream",
    "redshift_market_info_stream",
    "synthetic_paper_outcome_smoke",
}
EXCLUDED_SOURCE_TYPES = {"market_feed", "test"}

# Cap on the reported reward factor (returns profit factor) so an all-wins subject is a
# big-but-finite number rather than infinity.
_REWARD_FACTOR_CAP = 99.0


@dataclass(frozen=True)
class _Group:
    """Per-subject aggregate, accumulated in market terms before crossing the border."""

    source_id: str
    symbol: str
    side: str
    n: int = 0
    wins: int = 0
    ret_sum: float = 0.0
    ret_pos: float = 0.0
    ret_neg: float = 0.0


def _return_fraction(entry_price: Any, exit_price: Any, side: str) -> float | None:
    """Size-independent per-trade return, signed by direction. ``None`` if unusable.

    long:  (exit - entry) / entry   ·   short: (entry - exit) / entry
    """
    try:
        entry = float(entry_price)
        exit_ = float(exit_price)
    except (TypeError, ValueError):
        return None
    if entry <= 0:
        return None
    raw = (exit_ - entry) / entry
    return -raw if str(side).strip().lower() == "short" else raw


def _excluded(row: Mapping[str, Any]) -> bool:
    return (
        row.get("source_id") in EXCLUDED_SOURCE_IDS
        or (row.get("source_type") or "") in EXCLUDED_SOURCE_TYPES
    )


def _symbol_median_entries(rows: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    """Robust per-symbol median entry price, from valid non-excluded rows only."""
    entries: dict[str, list[float]] = {}
    for row in rows:
        if _excluded(row):
            continue
        try:
            ep = float(row.get("entry_price"))
        except (TypeError, ValueError):
            continue
        if ep > 0:
            entries.setdefault(str(row.get("symbol")), []).append(ep)
    return {
        sym: median(vals)
        for sym, vals in entries.items()
        if len(vals) >= MIN_SYMBOL_TRADES_FOR_ENTRY_CHECK
    }


def _is_corrupt_entry(row: Mapping[str, Any], symbol_median: Mapping[str, float]) -> bool:
    med = symbol_median.get(str(row.get("symbol")))
    if not med:
        return False
    try:
        ep = float(row.get("entry_price"))
    except (TypeError, ValueError):
        return False
    return ep > 0 and (ep > med * ENTRY_OUTLIER_RATIO or ep < med / ENTRY_OUTLIER_RATIO)


def clean_rows(rows: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Drop corrupt / excluded / duplicate rows; return the survivors and drop counts.

    This is where invariant #8 lives: implausible returns and entry-price outliers are
    discarded so a single mis-parsed price cannot manufacture a winning track record.
    """
    rows = list(rows)
    symbol_median = _symbol_median_entries(rows)
    kept: list[dict[str, Any]] = []
    counts = {"duplicate": 0, "excluded": 0, "corrupt_entry": 0, "corrupt_return": 0}
    for row in rows:
        if row.get("duplicate_of_event_id") is not None:
            counts["duplicate"] += 1
            continue
        if _excluded(row):
            counts["excluded"] += 1
            continue
        if _is_corrupt_entry(row, symbol_median):
            counts["corrupt_entry"] += 1
            continue
        ret = _return_fraction(row.get("entry_price"), row.get("exit_price"), row.get("side"))
        if ret is not None and abs(ret) > RETURN_SANITY_CAP:
            counts["corrupt_return"] += 1
            continue
        kept.append({**dict(row), "_return": ret})
    return kept, counts


def _age_days(exit_time: Any, now: datetime) -> float:
    try:
        ts = datetime.fromisoformat(str(exit_time).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return 0.0
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return max(0.0, (now - ts.astimezone(UTC)).total_seconds() / 86400.0)


def observations_by_subject(
    rows: Iterable[Mapping[str, Any]], *, now: datetime | None = None
) -> dict[str, list[Observation]]:
    """Translate cleaned outcome rows into neutral ``engine.edge`` observations per subject.

    The border crossing for the edge path: a market outcome becomes ``Observation(success,
    magnitude, age_days)`` — success = the return was positive, magnitude = the absolute
    return fraction, age = how long ago it closed. The engine never sees symbol or PnL.
    """
    now = now or datetime.now(UTC)
    out: dict[str, list[Observation]] = {}
    for row in rows:
        ret = row.get("_return")
        if ret is None:
            ret = _return_fraction(row.get("entry_price"), row.get("exit_price"), row.get("side"))
        if ret is None:
            continue
        key = setup_key(str(row.get("source_id")), str(row.get("symbol")), str(row.get("side")))
        out.setdefault(key, []).append(
            Observation(success=ret > 0, magnitude=abs(ret), age_days=_age_days(row.get("exit_time"), now))
        )
    return out


def _aggregate(rows: Iterable[Mapping[str, Any]]) -> dict[str, _Group]:
    groups: dict[str, _Group] = {}
    for row in rows:
        ret = row.get("_return")
        if ret is None:
            continue
        key = setup_key(str(row.get("source_id")), str(row.get("symbol")), str(row.get("side")))
        g = groups.get(key) or _Group(str(row.get("source_id")), str(row.get("symbol")), str(row.get("side")))
        groups[key] = _Group(
            source_id=g.source_id, symbol=g.symbol, side=g.side,
            n=g.n + 1,
            wins=g.wins + (1 if ret > 0 else 0),
            ret_sum=g.ret_sum + ret,
            ret_pos=g.ret_pos + (ret if ret > 0 else 0.0),
            ret_neg=g.ret_neg + (ret if ret < 0 else 0.0),
        )
    return groups


def _grade(g: _Group) -> dict[str, Any]:
    """Cross the border: turn a market aggregate into the neutral inputs the engine grades."""
    success_rate = g.wins / g.n if g.n else 0.0
    mean_reward = g.ret_sum / g.n if g.n else 0.0
    neg_abs = abs(g.ret_neg)
    if neg_abs > 0:
        reward_factor = min(g.ret_pos / neg_abs, _REWARD_FACTOR_CAP)
    elif g.ret_pos > 0:
        reward_factor = _REWARD_FACTOR_CAP
    else:
        reward_factor = 0.0
    composite = score.composite_score(success_rate, reward_factor, g.n)
    return {
        "key": setup_key(g.source_id, g.symbol, g.side),
        "source_id": g.source_id,
        "symbol": g.symbol,
        "side": g.side,
        "trades": g.n,
        "success_rate": round(success_rate, 4),
        "reward_factor": round(reward_factor, 4),
        "mean_reward": round(mean_reward, 6),
        "score": composite,
        "trust_tier": score.trust_tier(g.n),
        "decision": score.decision_tier(composite, g.n, mean_reward),
    }


def build_scoreboard(
    store: PaperOutcomeStore, *, lookback_days: int | None = None, now: datetime | None = None
) -> dict[str, Any]:
    """Build the per-subject scoreboard from a store's closed paper outcomes.

    Returns a dict with ``setups`` (a list of graded records), ``by_key`` (the same keyed by
    subject id, ready for the gate to look up), ``filtered`` (corruption drop counts), and
    ``generated_at``. Read-only.
    """
    now = now or datetime.now(UTC)
    since = (now - timedelta(days=lookback_days)).isoformat() if lookback_days else None
    rows = store.get_closed_outcomes_with_source(since=since)
    kept, counts = clean_rows(rows)
    setups = [_grade(g) for g in _aggregate(kept).values()]
    setups.sort(key=lambda s: s["trades"], reverse=True)
    return {
        "generated_at": now.isoformat(),
        "lookback_days": lookback_days,
        "setups": setups,
        "by_key": {s["key"]: s for s in setups},
        "filtered": counts,
    }


def edge_verdict_for(
    store: PaperOutcomeStore,
    source_id: str,
    symbol: str,
    side: str,
    *,
    now: datetime | None = None,
    **edge_kwargs: Any,
) -> EdgeVerdict:
    """Estimate the Bayesian edge for one setup from its (corruption-filtered) outcomes."""
    kept, _ = clean_rows(store.get_closed_outcomes_with_source())
    key = setup_key(source_id, symbol, side)
    observations = observations_by_subject(kept, now=now).get(key, [])
    edge = BayesianEdge(key, **edge_kwargs)
    edge.add_many(observations)
    return edge.verdict()


def assess_setup(
    store: PaperOutcomeStore,
    source_id: str,
    symbol: str,
    side: str,
    *,
    raw_commitment: float = 1.0,
    scoreboard: Mapping[str, Any] | None = None,
    min_n: int = gate.MIN_N_FOR_EXTREMES,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run the whole chain for one setup and return a receipt-compatible verdict.

    outcomes → neutral observations → edge estimate → scoreboard tier → gate multiplier.
    The returned dict carries the subject key, the edge verdict, the scoreboard record, and
    the gate ruling (tier + multiplier + adjusted commitment) — the single artifact a caller
    records. Read-only.
    """
    now = now or datetime.now(UTC)
    board = scoreboard if scoreboard is not None else build_scoreboard(store, now=now)
    key = setup_key(source_id, symbol, side)
    record = board.get("by_key", {}).get(key)

    edge_verdict = edge_verdict_for(store, source_id, symbol, side, now=now)
    gate_verdict = gate.evaluate(key, raw_commitment, record, min_n=min_n)

    return {
        "subject": key,
        "source_id": source_id,
        "symbol": symbol,
        "side": side,
        "edge": edge_verdict,
        "scoreboard": record,
        "tier": gate_verdict.tier,
        "multiplier": gate_verdict.multiplier,
        "raw_commitment": gate_verdict.raw_commitment,
        "adjusted_commitment": gate_verdict.adjusted_commitment,
        "gate_reason": gate_verdict.reason,
        "generated_at": now.isoformat(),
    }
