from __future__ import annotations

import numpy as np
import pandas as pd


def compute_divergence_features(prices: pd.DataFrame, ai_tickers: list[str]) -> pd.DataFrame:
    prices = prices.sort_index()
    available = [ticker for ticker in ai_tickers if ticker in prices.columns]
    if not available:
        return pd.DataFrame(index=prices.index)
    returns = prices[available].pct_change(fill_method=None).dropna(how="all")

    dispersion = returns.std(axis=1)

    rolling_corr = returns.rolling(63).corr()
    avg_corr = rolling_corr.groupby(level=0).mean().mean(axis=1)

    features = pd.DataFrame(
        {
            "ai_dispersion": dispersion,
            "ai_crowding_corr": avg_corr,
        }
    )
    return features
