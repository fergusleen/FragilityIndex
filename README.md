# AI Market Fragility Monitor

A transparent, local-first monitor that builds a weekly Fragility Index (0–100) from market, macro, and narrative signals. It focuses on regime stress and crowding rather than crash-date prediction.

## What it does
- Produces a weekly-updated composite index with component sub-scores and regime labels.
- Stores raw and curated data locally for reproducibility and auditability.
- Generates a static HTML report plus JSON/CSV outputs.
- Exposes a lightweight FastAPI for programmatic access.

## Quickstart
```bash
make install
cp config.example.toml config.toml
cp .env.example .env
fragility monitor --refresh --report out/
```

### Sample terminal output
```
Fragility Index
Index: 57.2 | Band: [44.8, 69.6]
Trend: .:-=++*##%%#**+=-::..

Components
- Capital Flow         61.3
- Revenue Reality      53.8
- Model Economics      48.9
- Narrative            62.4
- Macro Liquidity      59.1
- Dispersion           55.2
- Crowding             58.0
- Volatility           60.7
- Pricing Pressure     52.1
- Ai Hype              63.5

Report written to /path/to/out
```

### Sample output files
```
out/
  report.html
  summary.json
  timeseries.csv
  index.png
  components.png
```

## CLI
- `fragility monitor --asof YYYY-MM-DD --refresh --report out/`
- `fragility serve`

## Data sources
- Market prices: Stooq (free, no key). Optional hooks for paid providers via environment keys.
- Macro series: FRED (API key optional).
- Filings text: SEC EDGAR 10-K/10-Q documents.

## How the index works
1. **Feature engineering**: relative strength, dispersion, crowding, volatility regimes, macro risk, and narrative decay.
2. **Scoring**: rolling robust z-scores with winsorization, mapped to 0–100 via a logistic transform.
3. **Composite**: weighted average of core components with uncertainty bands.
4. **Explainability**: top component deltas drive the “Why this moved” bullets.

## Configuration
- `config.toml` controls tickers, weights, rolling windows, and report settings.
- `.env` holds optional API keys (FRED, etc.).

## Caveats
- Narrative signals are derived from filing text; these are slow-moving and noisy.
- Free fundamentals are not included by default; price-based proxies are used.
- Macro series availability can vary; the pipeline falls back to drawdown-based proxies.
