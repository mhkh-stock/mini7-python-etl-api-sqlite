"""Mini #7 — Python ETL: live weather API -> SQLite.

Extract: 7-day forecast for 6 Pakistani cities from the Open-Meteo
API (free, no key, no sign-up).
Transform: flatten the nested JSON into one tidy row per city per day.
Load: SQLite star-lite schema (fact_forecast + dim_city) with
data-quality checks run on every load.

This is a LIVE pipeline, not a seeded sample: re-running fetches fresh
forecasts, so the numbers change with the weather. The checks assert
structure and invariants (row counts, ranges, no duplicates) — never
fixed temperatures. The raw API responses are saved under data/raw/
so any run can be replayed offline.

Run:  python3 src/etl.py        (fetch + load)
      python3 src/checks.py     (verify the loaded database)
"""

import json
import sqlite3
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "weather.db"
SUMMARY = ROOT / "outputs" / "summary.md"

CITIES = [
    ("Lahore", 31.52, 74.36),
    ("Karachi", 24.86, 67.01),
    ("Islamabad", 33.68, 73.05),
    ("Peshawar", 34.01, 71.58),
    ("Quetta", 30.18, 67.01),
    ("Gilgit", 35.92, 74.31),
]
FORECAST_DAYS = 7
API = "https://api.open-meteo.com/v1/forecast"


def fetch(city, lat, lon):
    """One API call with a retry; returns the parsed JSON."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,"
                 "precipitation_sum,wind_speed_10m_max",
        "timezone": "Asia/Karachi",
        "forecast_days": FORECAST_DAYS,
    }
    last_err = None
    for attempt in (1, 2, 3):
        try:
            r = requests.get(API, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            last_err = e
            time.sleep(2 * attempt)
    raise RuntimeError(f"Open-Meteo failed for {city}: {last_err}")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    (ROOT / "outputs").mkdir(parents=True, exist_ok=True)
    run_date = date.today().isoformat()

    rows = []
    for city, lat, lon in CITIES:
        payload = fetch(city, lat, lon)
        (RAW / f"{city.lower()}_{run_date}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8")
        daily = payload["daily"]
        assert len(daily["time"]) == FORECAST_DAYS, f"{city}: short forecast"
        for i, d in enumerate(daily["time"]):
            rows.append({
                "city": city,
                "forecast_date": d,
                "temp_max_c": daily["temperature_2m_max"][i],
                "temp_min_c": daily["temperature_2m_min"][i],
                "precip_mm": daily["precipitation_sum"][i],
                "wind_max_kmh": daily["wind_speed_10m_max"][i],
                "run_date": run_date,
            })

    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    for city, lat, lon in CITIES:
        con.execute("INSERT INTO dim_city VALUES (?, ?, ?)", (city, lat, lon))
    con.executemany(
        "INSERT INTO fact_forecast VALUES "
        "(:city, :forecast_date, :temp_max_c, :temp_min_c, :precip_mm, "
        ":wind_max_kmh, :run_date)", rows)
    con.commit()

    n = con.execute("SELECT COUNT(*) FROM fact_forecast").fetchone()[0]
    hottest = con.execute(
        "SELECT city, MAX(temp_max_c) FROM fact_forecast "
        "GROUP BY city ORDER BY 2 DESC LIMIT 1").fetchone()
    coldest = con.execute(
        "SELECT city, MIN(temp_min_c) FROM fact_forecast "
        "GROUP BY city ORDER BY 2 ASC LIMIT 1").fetchone()
    wettest = con.execute(
        "SELECT city, SUM(precip_mm) FROM fact_forecast "
        "GROUP BY city ORDER BY 2 DESC LIMIT 1").fetchone()
    con.close()

    SUMMARY.write_text(
        f"# Mini #7 — Weather ETL run ({run_date})\n\n"
        f"Live 7-day forecast for 6 Pakistani cities, fetched from "
        f"Open-Meteo and loaded into `data/weather.db`.\n\n"
        f"- Rows loaded: **{n}** (6 cities x 7 days)\n"
        f"- Hottest day in the window: **{hottest[0]}**, "
        f"{hottest[1]:.1f} C max\n"
        f"- Coldest night in the window: **{coldest[0]}**, "
        f"{coldest[1]:.1f} C min\n"
        f"- Wettest week: **{wettest[0]}**, {wettest[1]:.1f} mm total\n\n"
        f"Re-run any time: `python3 src/etl.py` fetches a fresh "
        f"forecast; `python3 src/checks.py` verifies the load.\n",
        encoding="utf-8")
    print(f"loaded {n} rows for {run_date}")
    print(f"hottest: {hottest[0]} {hottest[1]:.1f}C | "
          f"coldest: {coldest[0]} {coldest[1]:.1f}C | "
          f"wettest: {wettest[0]} {wettest[1]:.1f}mm")


if __name__ == "__main__":
    main()
