import pandas as pd

from fragility_monitor.scoring.transforms import logistic_scale, normalize_score, rolling_robust_zscore, winsorize


def test_winsorize_clips() -> None:
    series = pd.Series([0, 1, 2, 100])
    clipped = winsorize(series, 0.0, 0.75)
    assert clipped.max() <= series.quantile(0.75)


def test_rolling_robust_zscore_returns_series() -> None:
    series = pd.Series(range(50))
    z = rolling_robust_zscore(series, window=20)
    assert len(z) == len(series)


def test_normalize_score_bounds() -> None:
    series = pd.Series(range(100))
    score = normalize_score(series, window=20, lower_q=0.05, upper_q=0.95)
    assert score.min() >= 0
    assert score.max() <= 100


def test_logistic_scale_center() -> None:
    scaled = logistic_scale(pd.Series([0.0]))
    assert abs(scaled.iloc[0] - 50) < 1e-6
