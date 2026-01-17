# AI Market Fragility Monitor
A weekly-updated instrument for monitoring fragility in AI-related equity markets. Hosted at https://fergusleen.github.io/FragilityIndex/

## What this is
This is a public, reproducible monitor of regime stress and its containment or propagation across market structure, liquidity, and narrative channels. It focuses on fragility signals rather than narratives. This does not predict crashes or timing.

## How to read it
The index ranges from Calm (0–20) to Fragile (80–100). A high component can coexist with a moderate composite because the model weights multiple channels; if stress has not propagated into volatility, crowding, or narrative, the composite stays contained. Use the banded view and component trendlines together, not any single point in isolation.

## Method (high level)
The index combines multiple transparent components using robust z-scores and fixed weights. There is no black-box ML. Data sources are public and results update weekly on a consistent cadence.

## What this is not
It is not investment advice, not a trading signal, and not a sentiment tracker.

## Publishing cadence
Updated weekly, with historical revisions visible in the charts. Live report: https://<username>.github.io/<repo>/

## Configuration
- `config.toml` controls tickers, weights, rolling windows, and report settings.
- `.env` holds optional API keys (FRED, etc.).

## Caveats
- Narrative signals are derived from filing text; these are slow-moving and noisy.
- Free fundamentals are not included by default; price-based proxies are used.
- Macro series availability can vary; the pipeline falls back to drawdown-based proxies.
