from __future__ import annotations

import pandas as pd

REGIME_LABELS = [
    (0, 20, "Calm"),
    (20, 40, "Warming"),
    (40, 60, "Elevated"),
    (60, 80, "Stressed"),
    (80, 100, "Fragile"),
]


def compute_composite(components: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    base_cols = [col for col in weights.keys() if col in components.columns]
    if not base_cols:
        raise ValueError("No components available for composite scoring")
    weight_series = pd.Series({col: weights[col] for col in base_cols})
    def weighted_row(row: pd.Series) -> float:
        available = row.dropna()
        if available.empty:
            return float("nan")
        row_weights = weight_series[available.index]
        row_weights = row_weights / row_weights.sum()
        return float((available * row_weights).sum())
    composite = components[base_cols].apply(weighted_row, axis=1)
    band = components[base_cols].std(axis=1, skipna=True)
    output = pd.DataFrame(
        {
            "index": composite,
            "band_lower": (composite - band).clip(lower=0),
            "band_upper": (composite + band).clip(upper=100),
        }
    )
    return output


def label_regime(value: float) -> str:
    for low, high, label in REGIME_LABELS:
        if low <= value < high:
            return label
    return REGIME_LABELS[-1][2]
