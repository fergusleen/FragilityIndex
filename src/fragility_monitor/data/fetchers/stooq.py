from __future__ import annotations

import io
import logging
from datetime import datetime

import pandas as pd
import requests

from fragility_monitor.data.fetchers.interfaces import MarketData

LOGGER = logging.getLogger(__name__)


class StooqFetcher:
    base_url = "https://stooq.pl/q/d/l/"

    def _symbol(self, ticker: str) -> str:
        clean = ticker.replace(".", "-").lower()
        return f"{clean}.us"

    def fetch_prices(self, tickers: list[str]) -> MarketData:
        frames = []
        for ticker in tickers:
            symbol = self._symbol(ticker)
            params = {"s": symbol, "i": "d"}
            resp = requests.get(self.base_url, params=params, timeout=30)
            resp.raise_for_status()
            df = pd.read_csv(io.BytesIO(resp.content))
            columns = {col.lower(): col for col in df.columns}
            date_col = columns.get("date") or columns.get("data")
            close_col = columns.get("close") or columns.get("zamkniecie")
            if not date_col or not close_col:
                LOGGER.warning("Stooq response missing columns for %s: %s", ticker, list(df.columns))
                continue
            df[date_col] = pd.to_datetime(df[date_col], utc=True, errors="coerce")
            df = df.rename(columns={date_col: "date", close_col: ticker})[["date", ticker]]
            df = df.dropna(subset=["date"])
            frames.append(df)
            LOGGER.info("Fetched %s (%s rows)", ticker, len(df))
        if not frames:
            return MarketData(prices=pd.DataFrame())
        merged = frames[0]
        for frame in frames[1:]:
            merged = merged.merge(frame, on="date", how="outer")
        merged = merged.sort_values("date").set_index("date")
        merged.index = merged.index.tz_convert(None)
        return MarketData(prices=merged)


def last_trading_date(df: pd.DataFrame) -> datetime | None:
    if df.empty:
        return None
    return df.index.max()
