"""foxclaw.engine.trust — diagnostic source scoring (invariant #5: weights, never caps).

Two orthogonal, domain-neutral signals, both Beta-posterior + down-weight-only:
  - reliability  (rho_source): did a source's claims later resolve usefully?
  - trustworthiness (rho_trust): are a source's claims well-formed, regardless of outcome?

Both stay SHADOW DIAGNOSTICS until promoted via the shadow-first ritual (invariant #2).
"""

from .reliability import ReliabilityVerdict, SourceReliability
from .trustworthiness import ClaimQuality, Trustworthiness, TrustVerdict, trust_haircut

__all__ = [
    "SourceReliability",
    "ReliabilityVerdict",
    "Trustworthiness",
    "ClaimQuality",
    "TrustVerdict",
    "trust_haircut",
]
