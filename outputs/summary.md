# Mini #7 — Weather ETL run (2026-11-06)

Live 7-day forecast for 6 Pakistani cities, fetched from Open-Meteo and loaded into `data/weather.db`.

- Rows loaded: **42** (6 cities x 7 days)
- Hottest day in the window: **Karachi**, 35.6 C max
- Coldest night in the window: **Gilgit**, 6.2 C min
- Wettest week: **Gilgit**, 8.5 mm total

Re-run any time: `python3 src/etl.py` fetches a fresh forecast; `python3 src/checks.py` verifies the load.
