from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from fragility_monitor.config import Config
from fragility_monitor.data.cache import ensure_dirs, read_parquet, write_parquet
from fragility_monitor.data.fetchers.fred import FredFetcher
from fragility_monitor.data.fetchers.sec_edgar import EdgarConfig, SecEdgarFetcher
from fragility_monitor.data.fetchers.stooq import StooqFetcher
from fragility_monitor.features.divergence import compute_divergence_features
from fragility_monitor.features.market import compute_market_features
from fragility_monitor.features.narrative import compute_narrative_features
from fragility_monitor.scoring.components import compute_component_scores
from fragility_monitor.scoring.composite import compute_composite, label_regime
from fragility_monitor.scoring.backtest import define_stress_events, evaluate_signals

LOGGER = logging.getLogger(__name__)


@dataclass
class MonitorResult:
    composite: pd.DataFrame
    components: pd.DataFrame
    summary: dict[str, Any]
    backtest: dict[str, float]


def _weekly(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.resample("W-FRI").last().ffill()


def _macro_features(macro: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    features = pd.DataFrame(index=prices.index)
    if "hy_spread" in macro.columns:
        features["hy_spread"] = macro["hy_spread"].reindex(features.index).ffill()
    else:
        spy = prices["SPY"].dropna()
        rolling_max = spy.rolling(63, min_periods=10).max()
        drawdown = (spy / rolling_max) - 1
        features["hy_spread"] = drawdown.reindex(features.index).ffill()
    if "vix" in macro.columns:
        features["vix"] = macro["vix"].reindex(features.index).ffill()
    return features


def _interpretation(score: float) -> str:
    regime = label_regime(score)
    if regime in {"Calm", "Warming"}:
        return "Signals suggest stable positioning with contained stress; monitor for divergence shifts."
    if regime == "Elevated":
        return "Fragility is building; crowding or narrative decay may be increasing sensitivity."
    if regime == "Stressed":
        return "Stress indicators are high; risk appetite appears fragile and crowding elevated."
    return "Market structure looks fragile; de-risking and narrative deterioration are pronounced."


def run_monitor(config: Config, refresh: bool = False) -> MonitorResult:
    raw_dir = Path(config.data["raw_dir"])
    curated_dir = Path(config.data["curated_dir"])
    ensure_dirs(raw_dir, curated_dir)

    tickers = list(dict.fromkeys(config.market["ai_tickers"] + config.market["benchmarks"]))

    market_path = curated_dir / "market_prices.parquet"
    if refresh or not market_path.exists():
        prices = StooqFetcher().fetch_prices(tickers).prices
        write_parquet(prices, market_path)
    else:
        prices = read_parquet(market_path) or pd.DataFrame()
    if prices.empty:
        raise RuntimeError("No market data fetched. Check network access or Stooq availability.")

    fred_fetcher = FredFetcher(api_key=config.fred.get("api_key"))
    macro_path = curated_dir / "macro_series.parquet"
    if refresh or not macro_path.exists():
        macro = fred_fetcher.fetch_series(config.fred.get("series", {})).series
        write_parquet(macro, macro_path)
    else:
        macro = read_parquet(macro_path) or pd.DataFrame()

    sec_path = curated_dir / "filing_signals.parquet"
    if refresh or not sec_path.exists():
        edgar_config = EdgarConfig(
            user_agent=config.sec["user_agent"],
            max_filings_per_ticker=int(config.sec["max_filings_per_ticker"]),
            cache_dir=raw_dir,
        )
        filings = SecEdgarFetcher(edgar_config).fetch_signals(config.market["ai_tickers"]).metrics
        write_parquet(filings, sec_path)
    else:
        filings = read_parquet(sec_path) or pd.DataFrame()

    market_features = compute_market_features(prices, config.market["ai_tickers"], benchmark="SPY")
    if market_features.empty:
        raise RuntimeError("Market features could not be computed from available price data.")
    divergence_features = compute_divergence_features(prices, config.market["ai_tickers"])
    narrative_features = compute_narrative_features(filings)
    macro_features = _macro_features(macro, prices)

    market_weekly = _weekly(market_features)
    divergence_weekly = _weekly(divergence_features)
    narrative_weekly = narrative_features.reindex(market_weekly.index).ffill(limit=13)
    macro_weekly = _weekly(macro_features)

    window_weeks = int(config.scoring["rolling_window_years"] * 52)
    lower_q, upper_q = config.scoring["winsorize_quantiles"]

    components = compute_component_scores(
        market_weekly,
        divergence_weekly,
        narrative_weekly,
        macro_weekly,
        window_weeks,
        lower_q,
        upper_q,
    )

    composite = compute_composite(components, config.weights)
    composite = composite.dropna(subset=["index"])
    if composite.empty:
        raise RuntimeError("Composite index is empty after scoring; check input data coverage.")

    index_value = float(composite["index"].iloc[-1])
    summary = {
        "asof": str(composite.index[-1].date()),
        "index": index_value,
        "regime": label_regime(index_value),
        "components": {k.replace("_", " ").title(): float(v) for k, v in components.iloc[-1].items()},
        "interpretation": _interpretation(index_value),
    }

    backtest = {}
    if "ai_returns" in market_features.columns:
        events = define_stress_events(market_features["ai_returns"])
        backtest = evaluate_signals(composite["index"], events)

    return MonitorResult(composite=composite, components=components, summary=summary, backtest=backtest)
