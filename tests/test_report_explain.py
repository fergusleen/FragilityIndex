import pandas as pd

from fragility_monitor.report.explain import (
    COMPONENT_LABELS,
    compute_movers,
    containment_message,
    label_component,
    stressed_triggers,
)


def test_label_component_expectation_load() -> None:
    assert label_component("expectation_load") == "Expectation Load"
    assert COMPONENT_LABELS["expectation_load"] == "Expectation Load"


def test_containment_message_includes_channels() -> None:
    latest = pd.Series(
        {
            "capital_flow": 95.0,
            "volatility": 20.0,
            "crowding": 30.0,
            "narrative": 10.0,
        }
    )
    message = containment_message(40.0, latest)
    assert message is not None
    assert "stress appears contained" in message
    assert "volatility" in message


def test_compute_movers_sigma_text() -> None:
    index = pd.date_range("2024-01-05", periods=120, freq="W-FRI")
    data = pd.DataFrame(
        {
            "capital_flow": range(120),
            "volatility": [value * 0.5 for value in range(120)],
        },
        index=index,
    )
    movers = compute_movers(data, window=52, top_n=2)
    assert movers
    assert any(mover.sigma_text for mover in movers)


def test_stressed_triggers_non_empty() -> None:
    index = pd.date_range("2024-01-05", periods=10, freq="W-FRI")
    components = pd.DataFrame(
        {
            "capital_flow": [50.0] * 10,
            "revenue_reality": [40.0] * 10,
            "crowding": [20.0] * 10,
            "volatility": [30.0] * 10,
            "narrative": [10.0] * 10,
        },
        index=index,
    )
    composite = pd.DataFrame({"index": [40.0] * 10}, index=index)
    triggers = stressed_triggers(components, composite)
    assert triggers
