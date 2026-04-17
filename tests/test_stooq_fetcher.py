from __future__ import annotations

import pandas as pd

from fragility_monitor.data.fetchers.stooq import StooqFetcher


class _Response:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def raise_for_status(self) -> None:
        return None


def test_fetch_prices_skips_malformed_csv(monkeypatch) -> None:
    responses = {
        "spy.us": _Response(b"Date,Open,High,Low,Close,Volume\n2026-04-16,500,505,498,503,100\n"),
        "nvda.us": _Response(b"Warning\nLine 2\nLine 3\nLine 4\nLine 5\nbad,line\n"),
    }

    def fake_get(url: str, params: dict[str, str], timeout: int) -> _Response:
        assert url == StooqFetcher.base_url
        assert timeout == 30
        return responses[params["s"]]

    monkeypatch.setattr("fragility_monitor.data.fetchers.stooq.requests.get", fake_get)

    prices = StooqFetcher().fetch_prices(["SPY", "NVDA"]).prices

    assert list(prices.columns) == ["SPY"]
    assert len(prices) == 1
    assert prices.index[0] == pd.Timestamp("2026-04-16")
    assert prices.loc[pd.Timestamp("2026-04-16"), "SPY"] == 503
