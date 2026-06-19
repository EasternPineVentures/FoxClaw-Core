"""Information quality scoring with separate, inspectable dimensions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InformationQualityInput:
    source_independence: int
    traceability: int
    freshness: int
    corroboration: int
    contradiction_penalty: int = 0


@dataclass(frozen=True)
class InformationQualityVerdict:
    evidence_quality: int
    source_independence: int
    traceability: int
    freshness: int
    corroboration: int
    contradiction_penalty: int
    reason_codes: tuple[str, ...]


def assess_information_quality(values: InformationQualityInput) -> InformationQualityVerdict:
    """Score evidence quality without collapsing its components in the output."""
    source_independence = _score(values.source_independence)
    traceability = _score(values.traceability)
    freshness = _score(values.freshness)
    corroboration = _score(values.corroboration)
    contradiction_penalty = _score(values.contradiction_penalty)
    base = round((source_independence + traceability + freshness + corroboration) / 4)
    penalty = int(contradiction_penalty * 0.35 + 0.5)
    evidence_quality = max(0, min(100, base - penalty))
    reasons: list[str] = []
    if source_independence < 50:
        reasons.append("weak_source_independence")
    if traceability < 50:
        reasons.append("weak_traceability")
    if freshness < 50:
        reasons.append("stale_evidence")
    if corroboration < 50:
        reasons.append("weak_corroboration")
    if contradiction_penalty >= 50:
        reasons.append("meaningful_opposition")
    return InformationQualityVerdict(
        evidence_quality=evidence_quality,
        source_independence=source_independence,
        traceability=traceability,
        freshness=freshness,
        corroboration=corroboration,
        contradiction_penalty=contradiction_penalty,
        reason_codes=tuple(reasons) or ("evidence_quality_measured",),
    )


def _score(value: int | float) -> int:
    return max(0, min(100, round(float(value))))
