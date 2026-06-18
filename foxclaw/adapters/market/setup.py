"""Market framing for a gate subject — the ``source:symbol:side`` key.

The engine gate (``engine.gate``) and the scoreboard grader (``engine.score``) speak of
an opaque *subject*. In the market domain a subject is a trade setup, identified by
``source_id:symbol:side`` — and ``symbol`` / ``side`` are market vocabulary, so the key
construction lives here in the adapter, never in ``engine/`` (invariant #4).

Split out of v1 ``tools/pre_decision_gate.py`` / ``tools/setup_performance_summary.py``,
which both inlined this same ``f"{source_id}:{symbol}:{side}"`` key — one definition now.
"""

from __future__ import annotations


def setup_key(source_id: str, symbol: str, side: str) -> str:
    """The canonical market subject key consumed by the engine gate/scoreboard.

    One definition of the setup identity, shared by the scoreboard builder (which writes
    it) and the gate caller (which looks it up), so the two cannot drift apart.
    """
    return f"{source_id}:{symbol}:{side}"
