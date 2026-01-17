from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import FastAPI

from fragility_monitor.config import Config
from fragility_monitor.monitor import run_monitor


def _serialize(df: pd.DataFrame) -> list[dict[str, Any]]:
    records = df.reset_index().rename(columns={"index": "date"}).to_dict(orient="records")
    for row in records:
        if "date" in row:
            row["date"] = pd.to_datetime(row["date"]).date().isoformat()
    return records


def create_app(config: Config) -> FastAPI:
    app = FastAPI(title="Fragility Monitor")

    @app.get("/index")
    def index() -> dict[str, Any]:
        result = run_monitor(config, refresh=False)
        latest = result.composite.iloc[-1].to_dict()
        latest["date"] = result.composite.index[-1].date().isoformat()
        return latest

    @app.get("/components")
    def components() -> dict[str, Any]:
        result = run_monitor(config, refresh=False)
        latest = result.components.iloc[-1].to_dict()
        latest["date"] = result.components.index[-1].date().isoformat()
        return latest

    @app.get("/timeseries")
    def timeseries() -> dict[str, Any]:
        result = run_monitor(config, refresh=False)
        payload = {
            "composite": _serialize(result.composite),
            "components": _serialize(result.components),
        }
        return payload

    return app


def run(config: Config, host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    app = create_app(config)
    uvicorn.run(app, host=host, port=port)
