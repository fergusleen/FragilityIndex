from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from fragility_monitor.report.explain import report_context
from fragility_monitor.scoring.composite import label_regime


def _plot_index(df: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df.index, df["index"], label="Fragility Index", color="#1f4e5f")
    ax.fill_between(df.index, df["band_lower"], df["band_upper"], color="#9ecae1", alpha=0.4)
    ax.set_title("Fragility Index")
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_components(components: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    for column in [
        "capital_flow",
        "revenue_reality",
        "model_economics",
        "narrative",
        "macro_liquidity",
        "expectation_load",
    ]:
        if column in components.columns:
            ax.plot(components.index, components[column], label=column.replace("_", " ").title())
    ax.set_title("Component Scores")
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def generate_report(
    output_dir: Path,
    composite: pd.DataFrame,
    components: pd.DataFrame,
    summary: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    index_plot = output_dir / "index.png"
    comp_plot = output_dir / "components.png"
    _plot_index(composite, index_plot)
    _plot_components(components, comp_plot)

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    timeseries_path = output_dir / "timeseries.csv"
    joined = composite.join(components, how="left")
    joined.to_csv(timeseries_path)

    env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))
    template = env.get_template("report.html")
    explain = report_context(composite, components, summary)
    html = template.render(
        index_plot=index_plot.name,
        components_plot=comp_plot.name,
        summary=summary,
        regime=label_regime(summary["index"]),
        movers=explain["movers"],
        containment_message=explain["containment_message"],
        macro_sector_callout=explain["macro_sector_callout"],
        stress_triggers=explain["stress_triggers"],
        summary_components=explain["summary_components"],
    )
    (output_dir / "report.html").write_text(html)
