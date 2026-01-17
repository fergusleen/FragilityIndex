from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from fragility_monitor.config import load_config
from fragility_monitor.logging import setup_logging
from fragility_monitor.monitor import run_monitor
from fragility_monitor.report.html import generate_report

LOGGER = logging.getLogger(__name__)


SPARK_CHARS = " .:-=+*#%@"


def sparkline(series: Iterable[float], width: int = 40) -> str:
    values = [float(value) for value in series if pd.notna(value)]
    if not values:
        return ""
    if len(values) > width:
        step = max(len(values) // width, 1)
        values = values[::step]
    min_val = min(values)
    max_val = max(values)
    if max_val - min_val == 0:
        return SPARK_CHARS[0] * len(values)
    chars = []
    for value in values:
        idx = int((value - min_val) / (max_val - min_val) * (len(SPARK_CHARS) - 1))
        chars.append(SPARK_CHARS[idx])
    return "".join(chars)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="fragility")
    sub = parser.add_subparsers(dest="command", required=True)

    monitor = sub.add_parser("monitor", help="Run the fragility monitor")
    monitor.add_argument("--asof", type=str, default=None)
    monitor.add_argument("--refresh", action="store_true")
    monitor.add_argument("--report", type=str, default=None)
    monitor.add_argument("--config", type=str, default=None)

    serve = sub.add_parser("serve", help="Run the API server")
    serve.add_argument("--host", type=str, default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--config", type=str, default=None)

    return parser.parse_args()


def _print_dashboard(composite: pd.DataFrame, components: pd.DataFrame) -> None:
    if composite.empty or components.empty:
        print("No data available for the requested window.")
        return
    latest = composite.iloc[-1]
    print("\nFragility Index")
    print(f"Index: {latest['index']:.1f} | Band: [{latest['band_lower']:.1f}, {latest['band_upper']:.1f}]")
    print(f"Trend: {sparkline(composite['index'].tail(60))}")
    print("\nComponents")
    for name, value in components.iloc[-1].items():
        print(f"- {name.replace('_', ' ').title():<20} {value:>5.1f}")


def main() -> None:
    args = _parse_args()
    config = load_config(args.config)
    setup_logging(config.general.get("log_level", "INFO"))

    if args.command == "monitor":
        result = run_monitor(config, refresh=args.refresh)
        if args.asof:
            asof_dt = datetime.fromisoformat(args.asof)
            result.composite = result.composite.loc[:asof_dt]
            result.components = result.components.loc[:asof_dt]
            if not result.composite.empty and not result.components.empty:
                result.summary["asof"] = str(result.composite.index[-1].date())
                result.summary["index"] = float(result.composite["index"].iloc[-1])
                result.summary["components"] = {
                    k.replace("_", " ").title(): float(v) for k, v in result.components.iloc[-1].items()
                }
        _print_dashboard(result.composite, result.components)
        if args.report:
            output_dir = Path(args.report)
            generate_report(output_dir, result.composite, result.components, result.summary)
            print(f"\nReport written to {output_dir.resolve()}")
    elif args.command == "serve":
        from fragility_monitor.api.server import run

        run(config, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
