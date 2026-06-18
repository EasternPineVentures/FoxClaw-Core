"""Small calibration helpers for Forecast Desk receipts."""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Iterable


def brier_score(probabilities: Iterable[Decimal], outcomes: Iterable[bool]) -> Decimal:
    probs = list(probabilities)
    outs = list(outcomes)
    if len(probs) != len(outs):
        raise ValueError("probabilities and outcomes must have the same length")
    if not probs:
        raise ValueError("at least one probability is required")
    total = Decimal("0")
    for prob, outcome in zip(probs, outs):
        if prob < 0 or prob > 1:
            raise ValueError("probability must be in [0, 1]")
        target = Decimal("1") if outcome else Decimal("0")
        total += (prob - target) ** 2
    return total / Decimal(len(probs))


def log_loss(probabilities: Iterable[Decimal], outcomes: Iterable[bool], *, epsilon: Decimal = Decimal("0.000001")) -> Decimal:
    probs = list(probabilities)
    outs = list(outcomes)
    if len(probs) != len(outs):
        raise ValueError("probabilities and outcomes must have the same length")
    if not probs:
        raise ValueError("at least one probability is required")
    total = 0.0
    eps = float(epsilon)
    for prob, outcome in zip(probs, outs):
        p = min(1.0 - eps, max(eps, float(prob)))
        total += -(math.log(p) if outcome else math.log(1.0 - p))
    return Decimal(str(total / len(probs)))
