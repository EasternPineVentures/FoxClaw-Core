from __future__ import annotations

from decimal import Decimal

import pytest

from foxclaw.adapters.event_contracts.calibration import brier_score, log_loss


def test_brier_score_for_binary_forecasts():
    score = brier_score([Decimal("0.80"), Decimal("0.20")], [True, False])
    assert score == Decimal("0.04")


def test_log_loss_requires_matching_lengths():
    with pytest.raises(ValueError):
        log_loss([Decimal("0.50")], [True, False])
