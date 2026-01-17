from __future__ import annotations

import numpy as np
import pandas as pd


def define_stress_events(returns: pd.Series) -> pd.Series:
    cumulative = (1 + returns.fillna(0)).cumprod()
    rolling_max = cumulative.rolling(63, min_periods=10).max()
    drawdown = (cumulative / rolling_max) - 1
    threshold = drawdown.quantile(0.1)
    return drawdown <= threshold


def evaluate_signals(index: pd.Series, events: pd.Series, threshold: float = 70.0, lead_days: int = 30) -> dict[str, float]:
    signals = index >= threshold
    event_dates = events[events].index
    if event_dates.empty:
        return {"precision": 0.0, "recall": 0.0, "avg_lead_days": float("nan")}
    true_positive = 0
    lead_times = []
    for event_date in event_dates:
        signal_window = signals.loc[:event_date].tail(lead_days)
        if signal_window.any():
            true_positive += 1
            lead = (event_date - signal_window[signal_window].index[-1]).days
            lead_times.append(lead)
    precision = true_positive / max(signals.sum(), 1)
    recall = true_positive / len(event_dates)
    avg_lead = float(np.mean(lead_times)) if lead_times else float("nan")
    return {"precision": precision, "recall": recall, "avg_lead_days": avg_lead}
