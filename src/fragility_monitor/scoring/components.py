from __future__ import annotations

import pandas as pd

from fragility_monitor.scoring.transforms import normalize_score


def _apply_score(series: pd.Series, window: int, lower_q: float, upper_q: float, invert: bool = False) -> pd.Series:
    if invert:
        series = -series
    return normalize_score(series, window, lower_q, upper_q)


def _safe_series(df: pd.DataFrame, name: str, index: pd.Index) -> pd.Series:
    if name in df.columns:
        return df[name].reindex(index)
    return pd.Series(index=index, dtype=float)


def compute_component_scores(
    market_features: pd.DataFrame,
    divergence_features: pd.DataFrame,
    narrative_features: pd.DataFrame,
    macro_features: pd.DataFrame,
    rolling_window: int,
    lower_q: float,
    upper_q: float,
) -> pd.DataFrame:
    df = pd.DataFrame(index=market_features.index)

    df["capital_flow"] = _apply_score(
        market_features["ai_relative_strength"], window=rolling_window, lower_q=lower_q, upper_q=upper_q
    )

    df["revenue_reality"] = _apply_score(
        market_features["ai_price_acceleration"], window=rolling_window, lower_q=lower_q, upper_q=upper_q
    )

    df["model_economics"] = _apply_score(
        market_features["ai_vol_of_vol"], window=rolling_window, lower_q=lower_q, upper_q=upper_q
    )

    df["narrative"] = _apply_score(
        _safe_series(narrative_features, "efficiency_transform_trend", df.index),
        window=rolling_window,
        lower_q=lower_q,
        upper_q=upper_q,
        invert=True,
    )

    df["macro_liquidity"] = _apply_score(
        _safe_series(macro_features, "hy_spread", df.index),
        window=rolling_window,
        lower_q=lower_q,
        upper_q=upper_q,
    )

    df["dispersion"] = _apply_score(
        divergence_features["ai_dispersion"], window=rolling_window, lower_q=lower_q, upper_q=upper_q
    )

    df["crowding"] = _apply_score(
        divergence_features["ai_crowding_corr"], window=rolling_window, lower_q=lower_q, upper_q=upper_q
    )

    df["volatility"] = _apply_score(
        market_features["ai_volatility"], window=rolling_window, lower_q=lower_q, upper_q=upper_q
    )

    df["pricing_pressure"] = _apply_score(
        _safe_series(narrative_features, "pricing_pressure", df.index),
        window=rolling_window,
        lower_q=lower_q,
        upper_q=upper_q,
    )

    df["ai_hype"] = _apply_score(
        _safe_series(narrative_features, "ai_density", df.index), window=rolling_window, lower_q=lower_q, upper_q=upper_q
    )

    df = df.sort_index()
    return df
