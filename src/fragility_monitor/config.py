from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

DEFAULT_CONFIG = {
    "general": {"base_currency": "USD", "log_level": "INFO"},
    "data": {"raw_dir": "data/raw", "curated_dir": "data/curated"},
    "market": {
        "ai_tickers": [
            "NVDA",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "AMD",
            "AVGO",
            "TSM",
            "ASML",
        ],
        "benchmarks": ["SPY", "QQQ"],
    },
    "fred": {"api_key": "", "series": {"hy_spread": "BAMLH0A0HYM2", "vix": "VIXCLS"}},
    "sec": {"user_agent": "FragilityMonitor/0.1 (email@example.com)", "max_filings_per_ticker": 4},
    "report": {"output_dir": "out"},
    "scoring": {"rolling_window_years": 2, "winsorize_quantiles": [0.05, 0.95]},
    "weights": {
        "capital_flow": 0.2,
        "revenue_reality": 0.15,
        "model_economics": 0.15,
        "narrative": 0.2,
        "macro_liquidity": 0.3,
    },
}


@dataclass
class Config:
    data: dict[str, Any]
    general: dict[str, Any]
    market: dict[str, Any]
    fred: dict[str, Any]
    sec: dict[str, Any]
    report: dict[str, Any]
    scoring: dict[str, Any]
    weights: dict[str, float]

    def path(self, *parts: str) -> Path:
        return Path(*parts)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path | None = None) -> Config:
    load_dotenv()
    config_data = DEFAULT_CONFIG
    if path:
        config_path = Path(path)
    else:
        config_path = Path("config.toml")
    if config_path.exists():
        with config_path.open("rb") as handle:
            user_config = tomllib.load(handle)
        config_data = _deep_merge(config_data, user_config)
    # env overrides
    fred_key = os.getenv("FRED_API_KEY")
    if fred_key:
        config_data["fred"]["api_key"] = fred_key
    return Config(
        data=config_data["data"],
        general=config_data["general"],
        market=config_data["market"],
        fred=config_data["fred"],
        sec=config_data["sec"],
        report=config_data["report"],
        scoring=config_data["scoring"],
        weights=config_data["weights"],
    )
