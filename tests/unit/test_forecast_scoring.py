from __future__ import annotations

from foxclaw.adapters.event_contracts.scoring import build_forecast_scoreboard


def test_scoreboard_includes_market_baseline_and_category_net():
    board = build_forecast_scoreboard(
        [
            {
                "category": "economics",
                "forecast_probability": "0.80",
                "market_probability": "0.60",
                "outcome_yes": True,
                "net_result": "2.00",
            },
            {
                "category": "economics",
                "forecast_probability": "0.30",
                "market_probability": "0.45",
                "outcome_yes": False,
                "net_result": "1.00",
            },
        ]
    )
    assert board["resolved_forecasts"] == 2
    assert board["brier_score"] == "0.0650"
    assert board["market_brier_score"] == "0.18125"
    assert board["by_category"]["economics"]["net_paper_result"] == "3.00"
