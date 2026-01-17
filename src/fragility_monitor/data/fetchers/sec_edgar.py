from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from fragility_monitor.data.fetchers.interfaces import FilingSignals

LOGGER = logging.getLogger(__name__)

SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"

AI_TERMS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "generative",
    "ai ",
]
EFFICIENCY_TERMS = [
    "efficiency",
    "cost",
    "optimization",
    "productivity",
    "automation",
]
TRANSFORM_TERMS = ["transform", "reimagine", "disruption", "revolution", "platform"]
PRICING_PRESSURE_TERMS = ["pricing pressure", "price pressure", "compression", "discount"]
RISK_TERMS = [
    "regulation",
    "headwinds",
    "competition",
    "slowdown",
    "margin pressure",
    "oversupply",
]


@dataclass
class EdgarConfig:
    user_agent: str
    max_filings_per_ticker: int
    cache_dir: Path


class SecEdgarFetcher:
    def __init__(self, config: EdgarConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

    def _cache_path(self, name: str) -> Path:
        return self.config.cache_dir / "sec" / name

    def _get_json(self, url: str, cache_name: str) -> Any:
        cache_path = self._cache_path(cache_name)
        if cache_path.exists():
            return json.loads(cache_path.read_text())
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(data))
        return data

    def _ticker_map(self) -> dict[str, str]:
        data = self._get_json(SEC_TICKER_URL, "company_tickers.json")
        mapping = {}
        for _, entry in data.items():
            mapping[entry["ticker"].upper()] = str(entry["cik_str"]).zfill(10)
        return mapping

    def _text_metrics(self, text: str) -> dict[str, float]:
        clean = re.sub(r"\s+", " ", text.lower())
        word_count = max(len(clean.split()), 1)
        def count_terms(terms: list[str]) -> int:
            return sum(clean.count(term) for term in terms)
        ai_count = count_terms(AI_TERMS)
        efficiency = count_terms(EFFICIENCY_TERMS)
        transform = count_terms(TRANSFORM_TERMS)
        pricing = count_terms(PRICING_PRESSURE_TERMS)
        risks = count_terms(RISK_TERMS)
        return {
            "ai_density": ai_count / word_count * 10000,
            "efficiency_transform_ratio": (efficiency + 1) / (transform + 1),
            "pricing_pressure": pricing / word_count * 10000,
            "risk_language": risks / word_count * 10000,
        }

    def _fetch_filing_text(self, cik: str, accession: str, document: str) -> str:
        url = ARCHIVES_URL.format(cik=str(int(cik)), accession=accession.replace("-", ""), document=document)
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    def fetch_signals(self, tickers: list[str]) -> FilingSignals:
        ticker_map = self._ticker_map()
        rows = []
        for ticker in tickers:
            cik = ticker_map.get(ticker.upper())
            if not cik:
                LOGGER.warning("No CIK found for %s", ticker)
                continue
            submissions = self._get_json(SUBMISSIONS_URL.format(cik=cik), f"submissions_{cik}.json")
            filings = submissions.get("filings", {}).get("recent", {})
            forms = filings.get("form", [])
            accession = filings.get("accessionNumber", [])
            documents = filings.get("primaryDocument", [])
            report_dates = filings.get("reportDate", [])
            filing_dates = filings.get("filingDate", [])
            count = 0
            for form, acc, doc, report_date, filing_date in zip(
                forms, accession, documents, report_dates, filing_dates
            ):
                if form not in {"10-K", "10-Q"}:
                    continue
                if count >= self.config.max_filings_per_ticker:
                    break
                try:
                    text = self._fetch_filing_text(cik, acc, doc)
                except Exception as exc:  # noqa: BLE001
                    LOGGER.warning("Failed to fetch filing %s %s: %s", ticker, acc, exc)
                    continue
                metrics = self._text_metrics(text)
                date = report_date or filing_date
                if not date:
                    continue
                rows.append({"date": date, "ticker": ticker, **metrics})
                count += 1
            LOGGER.info("Fetched %s filings for %s", count, ticker)
        if not rows:
            return FilingSignals(metrics=pd.DataFrame())
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], utc=True)
        df = df.sort_values("date").set_index("date")
        df.index = df.index.tz_convert(None)
        return FilingSignals(metrics=df)
