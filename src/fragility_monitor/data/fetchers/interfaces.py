from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd


@dataclass
class MarketData:
    prices: pd.DataFrame


@dataclass
class MacroData:
    series: pd.DataFrame


@dataclass
class FilingSignals:
    metrics: pd.DataFrame


class MarketFetcher(Protocol):
    def fetch_prices(self, tickers: list[str]) -> MarketData:
        ...


class MacroFetcher(Protocol):
    def fetch_series(self, series_map: dict[str, str]) -> MacroData:
        ...


class FilingFetcher(Protocol):
    def fetch_signals(self, tickers: list[str]) -> FilingSignals:
        ...
