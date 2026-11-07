# Mini #7 — Python ETL: Live Weather API → SQLite

**Repo:** https://github.com/mhkh-stock/mini7-python-etl-api-sqlite

**What it is:** a small, complete ETL pipeline. It fetches a 7-day
forecast for 6 Pakistani cities from the Open-Meteo API (free, no key,
no sign-up), flattens the JSON into tidy rows, loads them into SQLite,
and runs data-quality checks on every load.

**Why this mini exists:** Mini #1–#3 proved SQL on fixed data and
Mini #6 proved Excel formulas. This one proves the other half of the
job — **getting live data into a database reliably**: API calls with
retries, raw-response archiving, a written schema, and checks that
fail loudly when the source changes shape.

## Business question it answers

> "Can I trust a pipeline that pulls live data every day — and how
> would I know the moment it breaks?"

## What is inside

| File | What it does |
|---|---|
| `src/etl.py` | Extract (Open-Meteo API, 3 retries) → Transform (flatten daily JSON) → Load (SQLite) |
| `src/checks.py` | Data-quality checks as code — 16 checks, all passing |
| `sql/schema.sql` | `fact_forecast` + `dim_city` (PK: city + forecast_date) |
| `sql/analysis.sql` | 5 ready-to-run questions over the loaded data |
| `data/raw/*.json` | The raw API responses for this run — replayable offline |
| `data/weather.db` | The loaded database (rebuilt by every run; **not uploaded** — rebuildable from the scripts) |
| `outputs/summary.md` | This run's headline: hottest / coldest / wettest city |
| `LICENSE` | MIT licence, same as the other minis |
| `.gitignore` | Keeps the rebuilt `data/weather.db`, bytecode and local venvs out of the repo |

## Verified numbers (this run)

Run the pipeline to see today's numbers — they change with the
weather, which is the point. `outputs/summary.md` always holds the
latest run's headline figures.

## How to run it (under 5 steps)

1. `pip install -r requirements.txt`
2. `python3 src/etl.py` — fetches the forecast and loads the database.
3. `python3 src/checks.py` — 16 checks, all passing.
4. `sqlite3 data/weather.db < sql/analysis.sql` — the 5 analysis
   questions (hottest city, wettest week, biggest day-night swing…).
5. Re-run step 2 tomorrow: a fresh forecast loads, `run_date`
   stamps the new fetch, and the checks prove the new load is clean.

## What the checks prove (invariants, not fixed values)

A live pipeline cannot assert fixed temperatures — the weather
changes. So the checks assert what must *always* be true: 6 cities ×
7 days = 42 rows, one `run_date` only, forecast window `run_date` →
+6 days, max ≥ min on every row, temperatures in a plausible Pakistan
range (−10 to 55 °C), no negatives, no nulls, no orphans, and the raw
JSON files on disk hold the same 42 days that were loaded. The date
checks anchor to the `run_date` stored in the database, not to
today's date, so they verify any stored run on any later day — a
clone checked tomorrow still goes green.

## Data dictionary

| Table | Column | Type | Meaning |
|---|---|---|---|
| `dim_city` | `city` | TEXT PK | City name (Lahore, Karachi, Islamabad, Peshawar, Quetta, Gilgit) |
|  | `latitude` | REAL NOT NULL | Requested latitude (decimal degrees) |
|  | `longitude` | REAL NOT NULL | Requested longitude (decimal degrees) |
| `fact_forecast` | `city` | TEXT NOT NULL, FK → `dim_city` | City the row belongs to |
|  | `forecast_date` | TEXT NOT NULL (`YYYY-MM-DD`) | The day being forecast; PK is (`city`, `forecast_date`) |
|  | `temp_max_c` | REAL NOT NULL | Forecast daily maximum temperature, °C |
|  | `temp_min_c` | REAL NOT NULL | Forecast daily minimum temperature, °C |
|  | `precip_mm` | REAL NOT NULL | Forecast daily precipitation total, mm |
|  | `wind_max_kmh` | REAL NOT NULL | Forecast daily maximum wind speed at 10 m, km/h |
|  | `run_date` | TEXT NOT NULL (`YYYY-MM-DD`) | The date the forecast was fetched; stamps the run |

One row per city per day: 6 cities × 7 days = 42 rows per run.

## Tools

- Python 3 + requests (the only dependency, pinned in `requirements.txt`)
- Open-Meteo API — free, no key: `https://open-meteo.com`
- SQLite

## Limits

- **Forecast, not observed weather.** These are model forecasts for
  the next 7 days, not measurements; re-running on a later day gives
  different numbers, which is the point.
- **One run kept.** Every run rebuilds `data/weather.db`, so only the
  latest forecast is in the database. History lives in `data/raw/`,
  which keeps one JSON file per city per run date — nothing is
  deleted there, so old files accumulate across runs.
- **7-day window only.** `forecast_days` is fixed at 7; longer
  windows need a code change, not a flag.
- **6 API calls per run, well inside the free tier.** Open-Meteo's
  free tier allows 10,000 calls/day with no key or sign-up; this
  pipeline makes exactly one call per city.
- **Coordinates snap to the nearest model grid cell.** The raw JSON
  echoes the latitude/longitude actually used, which differ slightly
  (up to ~0.06°) from the city-centre coordinates in `src/etl.py`.
- **Data licence: CC BY 4.0.** Open-Meteo data is free to use and
  redistribute, including commercially, with attribution — so this
  project credits Open-Meteo wherever its data appears.

## Data source note

**Live public data.** Open-Meteo forecast API, fetched at run time;
nothing is sampled or invented. Cities: Lahore, Karachi, Islamabad,
Peshawar, Quetta, Gilgit. The raw responses are saved so any run can
be audited after the fact. Weather data by Open-Meteo
([open-meteo.com](https://open-meteo.com), CC BY 4.0).
