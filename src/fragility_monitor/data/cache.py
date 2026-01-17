from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def ensure_dirs(*paths: str | Path) -> None:
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def write_raw(path: Path, content: bytes) -> None:
    ensure_dirs(path.parent)
    path.write_bytes(content)


def read_raw(path: Path) -> bytes | None:
    if path.exists():
        return path.read_bytes()
    return None


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    ensure_dirs(path.parent)
    df.to_parquet(path, index=True)


def read_parquet(path: Path) -> pd.DataFrame | None:
    if path.exists():
        return pd.read_parquet(path)
    return None


def list_cached(paths: Iterable[Path]) -> list[Path]:
    return [path for path in paths if path.exists()]
