from __future__ import annotations

import numpy as np
import pandas as pd


def compute_narrative_features(filings: pd.DataFrame) -> pd.DataFrame:
    if filings.empty:
        return pd.DataFrame()
    filings = filings.sort_index()
    normalized = filings.copy()
    for column in ["ai_density", "pricing_pressure", "risk_language"]:
        normalized[column] = normalized.groupby("ticker")[column].transform(
            lambda series: (series - series.mean()) / (series.std(ddof=0) or 1.0)
        )
    grouped = normalized.groupby("date").mean(numeric_only=True).sort_index()
    grouped = grouped.resample("W-FRI").ffill(limit=13)

    ratio_smoothed = grouped["efficiency_transform_ratio"].rolling(4, min_periods=1).mean()
    ratio_trend = ratio_smoothed.pct_change(13).fillna(0.0)

    features = pd.DataFrame(
        {
            "ai_density": grouped["ai_density"],
            "efficiency_transform_trend": ratio_trend,
            "pricing_pressure": grouped["pricing_pressure"],
            "risk_language": grouped["risk_language"],
        }
    )
    features = features.replace([np.inf, -np.inf], np.nan)
    return features.fillna(0.0)
