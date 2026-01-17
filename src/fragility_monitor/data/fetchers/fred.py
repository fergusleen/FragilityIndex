from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import requests

from fragility_monitor.data.fetchers.interfaces import MacroData

LOGGER = logging.getLogger(__name__)


class FredFetcher:
    base_url = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or ""

    def _fetch_series(self, series_id: str) -> pd.DataFrame:
        params: dict[str, Any] = {
            "series_id": series_id,
            "file_type": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key
        try:
            resp = requests.get(self.base_url, params=params, timeout=30)
            resp.raise_for_status()
        except requests.HTTPError as exc:
            LOGGER.warning("FRED request failed for %s: %s", series_id, exc)
            return pd.DataFrame()
        data = resp.json()
        observations = data.get("observations", [])
        df = pd.DataFrame(observations)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"], utc=True)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df[["date", "value"]]

    def fetch_series(self, series_map: dict[str, str]) -> MacroData:
        frames = []
        for name, series_id in series_map.items():
            df = self._fetch_series(series_id)
            if df.empty:
                LOGGER.warning("No data for FRED series %s", series_id)
                continue
            df = df.rename(columns={"value": name})
            frames.append(df)
        if not frames:
            return MacroData(series=pd.DataFrame())
        merged = frames[0]
        for frame in frames[1:]:
            merged = merged.merge(frame, on="date", how="outer")
        merged = merged.sort_values("date").set_index("date")
        merged.index = merged.index.tz_convert(None)
        return MacroData(series=merged)
