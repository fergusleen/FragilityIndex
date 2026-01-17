from __future__ import annotations

import pandas as pd


def align_on_index(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    combined = frames[0]
    for frame in frames[1:]:
        combined = combined.join(frame, how="outer")
    return combined.sort_index()
