from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

COMPONENT_LABELS: dict[str, str] = {
    "capital_flow": "Capital Flow",
    "revenue_reality": "Revenue Reality",
    "model_economics": "Model Economics",
    "narrative": "Narrative",
    "macro_liquidity": "Macro Liquidity",
    "dispersion": "Dispersion",
    "crowding": "Crowding",
    "volatility": "Volatility",
    "pricing_pressure": "Pricing Pressure",
    "expectation_load": "Expectation Load",
}

PROPAGATION_CHANNELS = {
    "volatility": (35.0, "volatility"),
    "crowding": (35.0, "crowding"),
    "narrative": (20.0, "narrative"),
}


@dataclass
class Mover:
    name: str
    delta: float
    sigma: float | None

    @property
    def sigma_text(self) -> str:
        if self.sigma is None or np.isnan(self.sigma):
            return ""
        return f"{self.sigma:+.1f}σ"


def label_component(name: str) -> str:
    return COMPONENT_LABELS.get(name, name.replace("_", " ").title())


def compute_movers(components: pd.DataFrame, window: int = 104, top_n: int = 5) -> list[Mover]:
    if len(components) < 2:
        return []
    deltas = components.diff()
    latest_delta = deltas.iloc[-1]
    rolling_std = deltas.rolling(window, min_periods=10).std().iloc[-1]
    movers = []
    for name, delta in latest_delta.items():
        if pd.isna(delta):
            continue
        sigma = None
        std = rolling_std.get(name)
        if std is not None and not np.isnan(std):
            sigma = float(delta / std) if std != 0 else 0.0
        movers.append(Mover(name=label_component(name), delta=float(delta), sigma=sigma))
    movers.sort(key=lambda mover: abs(mover.delta), reverse=True)
    return movers[:top_n]


def containment_message(composite_value: float, components_latest: pd.Series) -> str | None:
    if composite_value >= 50:
        return None
    if components_latest.max(skipna=True) <= 90:
        return None
    calm = []
    for key, (threshold, label) in PROPAGATION_CHANNELS.items():
        value = components_latest.get(key)
        if value is not None and value < threshold:
            calm.append(label)
    if not calm:
        return "One component is maxed, but propagation channels remain muted; the stress appears contained."
    calm_list = ", ".join(calm)
    return (
        "One component is maxed, but it has not yet propagated into "
        f"{calm_list}; the stress appears contained."
    )


def macro_sector_callout(components_latest: pd.Series) -> str | None:
    macro = components_latest.get("macro_liquidity")
    capital = components_latest.get("capital_flow")
    revenue = components_latest.get("revenue_reality")
    if macro is None or capital is None or revenue is None:
        return None
    if macro < 35 and (capital > 60 or revenue > 60):
        return (
            "Macro conditions are relatively calm; current fragility appears sector-specific "
            "(idiosyncratic) rather than systemic."
        )
    return None


def stressed_triggers(components: pd.DataFrame, composite: pd.DataFrame) -> list[str]:
    triggers: list[str] = []
    latest = components.iloc[-1]
    crowding = latest.get("crowding")
    if crowding is None or crowding < 50 or (components["crowding"].tail(3) <= 50).any():
        triggers.append("Crowding above 50 for three consecutive weeks.")

    volatility = latest.get("volatility")
    if volatility is None or volatility < 55:
        triggers.append("Volatility score above 55.")

    narrative = latest.get("narrative")
    if narrative is None or narrative < 30:
        triggers.append("Narrative score above 30.")

    capital = latest.get("capital_flow")
    if capital is None or capital < 75 or components["capital_flow"].tail(3).diff().sum() <= 0:
        triggers.append("Capital Flow above 75 with a rising 3-week trend.")

    if len(composite) >= 4:
        trend_3w = composite["index"].iloc[-1] - composite["index"].iloc[-4]
        if trend_3w < 15:
            triggers.append("Composite index up 15+ points over three weeks.")

    revenue = latest.get("revenue_reality")
    if revenue is None or revenue < 70:
        triggers.append("Revenue Reality above 70.")

    return triggers[:6]


def report_context(composite: pd.DataFrame, components: pd.DataFrame, summary: dict[str, Any]) -> dict[str, Any]:
    latest_components = components.iloc[-1]
    composite_value = float(composite["index"].iloc[-1])
    movers = compute_movers(components)
    return {
        "movers": movers,
        "containment_message": containment_message(composite_value, latest_components),
        "macro_sector_callout": macro_sector_callout(latest_components),
        "stress_triggers": stressed_triggers(components, composite),
        "component_labels": {key: label_component(key) for key in components.columns},
        "summary_components": {
            label_component(key): float(value) for key, value in latest_components.items()
        },
    }
