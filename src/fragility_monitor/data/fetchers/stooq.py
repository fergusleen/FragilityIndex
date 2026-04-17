from __future__ import annotations

import io
import logging
from datetime import datetime

import pandas as pd
import requests
from pandas.errors import EmptyDataError, ParserError

from fragility_monitor.data.fetchers.interfaces import MarketData

LOGGER = logging.getLogger(__name__)


class StooqFetcher:
    base_url = "https://stooq.pl/q/d/l/"

    def _symbol(self, ticker: str) -> str:
        clean = ticker.replace(".", "-").lower()
        return f"{clean}.us"

    def _parse_response(self, ticker: str, content: bytes) -> pd.DataFrame | None:
        preview = content[:200].decode("utf-8", errors="replace").strip()
        if not preview:
            LOGGER.warning("Stooq returned an empty response for %s", ticker)
            return None
        if preview.startswith("<") or "<html" in preview.lower():
            LOGGER.warning("Stooq returned non-CSV content for %s: %r", ticker, preview[:120])
            return None
        try:
            return pd.read_csv(io.BytesIO(content))
        except (EmptyDataError, ParserError, UnicodeDecodeError) as exc:
            LOGGER.warning("Failed to parse Stooq response for %s: %s; preview=%r", ticker, exc, preview[:120])
            return None

    def fetch_prices(self, tickers: list[str]) -> MarketData:
        frames = []
        for ticker in tickers:
            symbol = self._symbol(ticker)
            params = {"s": symbol, "i": "d"}
            try:
                resp = requests.get(self.base_url, params=params, timeout=30)
                resp.raise_for_status()
            except requests.RequestException as exc:
                LOGGER.warning("Failed to fetch %s from Stooq: %s", ticker, exc)
                continue
            df = self._parse_response(ticker, resp.content)
            if df is None or df.empty:
                LOGGER.warning("Skipping %s due to unusable Stooq payload", ticker)
                continue
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
