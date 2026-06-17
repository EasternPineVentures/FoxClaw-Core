"""foxclaw.contract — the public airlock.

This is the ONLY surface that CoinFox and any public node may import. It exposes
read-only, sanitized views and the types to read them — never engine internals,
keys, raw private data, or any write path. If a capability is not published here,
the public layer cannot reach it.

Planned surface (Phase 1):
    scoreboard_snapshot()      -> public-safe per-setup performance
    decision_receipt_view(id)  -> a redacted, auditable receipt
    market_pulse()             -> context-only market summary
    source_memory_snapshot()   -> context-only channel/source memory
    capabilities()             -> capability descriptor (can_*: False by default)

Nothing is wired yet — the engine ports in first (see docs/architecture.md).
"""
from __future__ import annotations

__all__: list[str] = []
