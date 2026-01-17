import pandas as pd

from fragility_monitor.scoring.components import compute_component_scores


def test_component_scores_shape() -> None:
    index = pd.date_range("2020-01-03", periods=30, freq="W-FRI")
    market = pd.DataFrame(
        {
            "ai_relative_strength": range(30),
            "ai_price_acceleration": range(30),
            "ai_vol_of_vol": range(30),
            "ai_volatility": range(30),
        },
        index=index,
    )
    divergence = pd.DataFrame(
        {"ai_dispersion": range(30), "ai_crowding_corr": range(30)}, index=index
    )
    narrative = pd.DataFrame(
        {"efficiency_transform_trend": range(30), "pricing_pressure": range(30), "ai_density": range(30)},
        index=index,
    )
    macro = pd.DataFrame({"hy_spread": range(30)}, index=index)

    scores = compute_component_scores(market, divergence, narrative, macro, 12, 0.05, 0.95)
    assert not scores.empty
    assert "capital_flow" in scores.columns
