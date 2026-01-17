from __future__ import annotations

import pandas as pd


def compute_market_features(prices: pd.DataFrame, ai_tickers: list[str], benchmark: str = "SPY") -> pd.DataFrame:
    prices = prices.sort_index()
    available = [ticker for ticker in ai_tickers if ticker in prices.columns]
    if not available:
        return pd.DataFrame(index=prices.index)
    returns = prices.pct_change(fill_method=None).dropna(how="all")
    ai_returns = returns[available].mean(axis=1)
    bench_returns = returns[benchmark] if benchmark in returns else returns.mean(axis=1)

    ai_price = prices[available].mean(axis=1)
    ai_momentum = ai_price.pct_change(21)
    ai_acceleration = ai_momentum.diff(21)
    ai_realized_vol = ai_returns.rolling(21).std() * (252 ** 0.5)
    vol_of_vol = ai_realized_vol.rolling(21).std()

    relative_strength = (ai_returns - bench_returns).rolling(21).sum()

    features = pd.DataFrame(
        {
            "ai_relative_strength": relative_strength,
            "ai_price_acceleration": ai_acceleration,
            "ai_volatility": ai_realized_vol,
            "ai_vol_of_vol": vol_of_vol,
            "ai_returns": ai_returns,
            "bench_returns": bench_returns,
        }
    )
    return features
