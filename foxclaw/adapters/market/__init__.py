"""foxclaw.adapters.market — OHLCV / venue / price feeds, and market domain rules.

The ONLY place market vocabulary lives (invariant #4). Holds the market's definition
of a well-formed claim, consumed by the domain-neutral engine.trust.Trustworthiness.
"""

from .claims import market_claim_well_formed

__all__ = ["market_claim_well_formed"]
