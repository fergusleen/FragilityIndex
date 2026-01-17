from __future__ import annotations

import numpy as np
import pandas as pd


def winsorize(series: pd.Series, lower: float, upper: float) -> pd.Series:
    low = series.quantile(lower)
    high = series.quantile(upper)
    return series.clip(lower=low, upper=high)


def rolling_robust_zscore(series: pd.Series, window: int) -> pd.Series:
    def _robust_z(x: pd.Series) -> float:
        median = x.median()
        mad = (x - median).abs().median()
        scale = 1.4826 * mad if mad > 0 else x.std(ddof=0)
        if scale == 0 or np.isnan(scale):
            return 0.0
        return (x.iloc[-1] - median) / scale

    return series.rolling(window, min_periods=max(10, window // 4)).apply(_robust_z, raw=False)


def logistic_scale(z: pd.Series) -> pd.Series:
    clipped = z.clip(lower=-20, upper=20)
    return 100 * (1 / (1 + np.exp(-clipped)))


def normalize_score(series: pd.Series, window: int, lower_q: float, upper_q: float) -> pd.Series:
    clean = winsorize(series.dropna(), lower_q, upper_q)
    aligned = series.copy()
    aligned.loc[clean.index] = clean
    z = rolling_robust_zscore(aligned, window)
    score = logistic_scale(z)
    return score.replace([np.inf, -np.inf], np.nan)
