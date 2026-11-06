# Mini #7 — Python ETL: Live Weather API → SQLite

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
7 days = 42 rows, one `run_date` only, forecast window today → +6
days, max ≥ min on every row, temperatures in a plausible Pakistan
range (−10 to 55 °C), no negatives, no nulls, no orphans, and the raw
JSON files on disk hold the same 42 days that were loaded.

## Tools

- Python 3 + requests (the only dependency)
- Open-Meteo API — free, no key: `https://open-meteo.com`
- SQLite

## Data source note

**Live public data.** Open-Meteo forecast API, fetched at run time;
nothing is sampled or invented. Cities: Lahore, Karachi, Islamabad,
Peshawar, Quetta, Gilgit. The raw responses are saved so any run can
be audited after the fact.
