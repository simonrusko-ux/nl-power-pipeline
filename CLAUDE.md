# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`nl-power-pipeline` — a local Python data pipeline that ingests hourly Dutch weather (Open-Meteo) and day-ahead electricity prices + wind/solar generation (Energy-Charts API by Fraunhofer ISE), stores everything in DuckDB, and visualizes weather → renewables → price relationships in a Streamlit dashboard. Bonus phase: next-day price prediction (baselines → LightGBM, time-based split only). Full spec lives in the project owner's notes (v2.0, July 2026).

Both APIs are public JSON, no auth. Everything runs locally; no deployment, no streaming.

## Commands

- `python run_pipeline.py` — full run: ingest → transform → quality checks (single entry point)
- `python run_pipeline.py --backfill YYYY-MM-DD` — backfill history from date, in monthly windows
- `streamlit run app/dashboard.py` — dashboard
- `pytest` — tests (parsing, dedup, checks)

Dependencies (pyproject.toml): httpx, tenacity, duckdb, streamlit, pandas, plotly.

## Project structure

```
weather-project/
├── run_pipeline.py          # orchestrator: ingest → transform → checks
├── ingest/
│   ├── __init__.py
│   ├── client.py            # shared: httpx setup, retry, pauses
│   ├── openmeteo.py         # fetch weather → write JSON to raw
│   └── energy_charts.py     # prices + generation → raw
├── transform/
│   ├── runner.py            # thin Python: loads .sql files and runs them
│   ├── staging.sql          # parsing lives HERE: JSON from raw → typed tables
│   └── marts.sql            # staging → hourly_wide, daily_summary
├── quality/
│   └── checks.py            # checks over finished tables
├── app/
│   └── dashboard.py         # Streamlit
├── tests/
│   ├── test_staging.py      # parsing and dedup — over small JSON samples
│   └── test_checks.py
├── data/                    # warehouse.duckdb (gitignored)
└── pyproject.toml
```

Ingest never parses response bodies — it only fetches and stores originals (plus HTTP status). All parsing happens in SQL in staging.

## Architecture: three-layer DuckDB warehouse

Data flows API → `raw` → `staging` → `marts`, all in `data/warehouse.duckdb` (gitignored):

- **raw** — append-only, never deleted. `raw.api_calls` stores full JSON response bodies + request metadata, so parsing can be redone from originals without new API calls.
- **staging** (`stg.weather_hourly`, `stg.prices`, `stg.generation`) — typed, UTC, deduplicated. Rebuilt via full refresh from raw on every run (`transform/staging.sql`).
- **marts** (`mart.hourly_wide`, `mart.daily_summary`) — one row per hour, weather averaged across 4 locations, 15-min prices/generation aggregated to hourly (`transform/marts.sql`).

Key invariants that hold the design together:

- **Idempotency via overlap + dedup:** incremental runs deliberately re-fetch overlapping windows (last 7 days); staging dedupes with `ROW_NUMBER() OVER (PARTITION BY pk ORDER BY ingested_at DESC)` — newest wins, so measurements replace forecasts and corrections replace originals. Running the pipeline twice must never duplicate or break anything.
- **UTC everywhere internally** (`timezone=UTC` on all API requests); local time (Europe/Amsterdam) exists only as a derived column in marts. Energy-Charts timestamps are `unix_seconds` — interpret as UTC.
- **Raw keeps original resolution** (prices/generation may be 15-min); hourly aggregation happens only in marts.
- **Quality checks gate every run** (`quality/checks.py`): hour completeness, PK uniqueness, value ranges, freshness ≤ 48 h. Failure → non-zero exit code.

## Ingest conventions

- httpx with 30 s timeout; tenacity exponential backoff (1→2→4→8 s, max 5 attempts) retried only on network errors and 5xx/429 — other 4xx fail fast.
- ≥1 s pause between requests to the same host; backfill in monthly windows (free public APIs, be polite).
- Open-Meteo archive API lags ~5 days behind reality — recent days come from the forecast endpoint (`past_days`), flagged `is_forecast` in staging.
- `logging` module, never `print`.

