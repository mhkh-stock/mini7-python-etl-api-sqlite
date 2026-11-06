"""Data-quality checks for Mini #7 (run: python3 src/checks.py).

These assert STRUCTURE and INVARIANTS of a live pipeline — never fixed
temperatures, because a re-run fetches a fresh forecast. If the API
shape changes or the load corrupts, these fail loudly.
"""

import json
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "weather.db"
RAW = ROOT / "data" / "raw"
SUMMARY = ROOT / "outputs" / "summary.md"

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name} {detail}")


check("database exists", DB.exists())
con = sqlite3.connect(DB)
check("6 cities in dim_city",
      con.execute("SELECT COUNT(*) FROM dim_city").fetchone()[0] == 6)
check("42 forecast rows (6 cities x 7 days)",
      con.execute("SELECT COUNT(*) FROM fact_forecast").fetchone()[0] == 42)
check("one run_date only (no mixed runs)",
      con.execute("SELECT COUNT(DISTINCT run_date) FROM fact_forecast")
      .fetchone()[0] == 1)
check("run_date is today",
      con.execute("SELECT DISTINCT run_date FROM fact_forecast")
      .fetchone()[0] == date.today().isoformat())
check("7 distinct forecast dates per city",
      con.execute("SELECT MIN(cnt) FROM (SELECT COUNT(DISTINCT forecast_date) "
                  "AS cnt FROM fact_forecast GROUP BY city)").fetchone()[0] == 7)
check("forecast window starts today",
      con.execute("SELECT MIN(forecast_date) FROM fact_forecast")
      .fetchone()[0] == date.today().isoformat())
check("forecast window ends 6 days out",
      con.execute("SELECT MAX(forecast_date) FROM fact_forecast")
      .fetchone()[0] == (date.today() + timedelta(days=6)).isoformat())
check("no nulls in any measure",
      con.execute("SELECT COUNT(*) FROM fact_forecast WHERE temp_max_c IS NULL "
                  "OR temp_min_c IS NULL OR precip_mm IS NULL "
                  "OR wind_max_kmh IS NULL").fetchone()[0] == 0)
check("max >= min on every row",
      con.execute("SELECT COUNT(*) FROM fact_forecast "
                  "WHERE temp_max_c < temp_min_c").fetchone()[0] == 0)
check("temperatures in plausible Pakistan range (-10 to 55 C)",
      con.execute("SELECT COUNT(*) FROM fact_forecast WHERE temp_max_c > 55 "
                  "OR temp_min_c < -10").fetchone()[0] == 0)
check("precipitation and wind never negative",
      con.execute("SELECT COUNT(*) FROM fact_forecast WHERE precip_mm < 0 "
                  "OR wind_max_kmh < 0").fetchone()[0] == 0)
check("no orphan rows (every city in dim_city)",
      con.execute("SELECT COUNT(*) FROM fact_forecast f LEFT JOIN dim_city c "
                  "ON c.city = f.city WHERE c.city IS NULL").fetchone()[0] == 0)

# Raw responses on disk match what was loaded.
today = date.today().isoformat()
raw_files = sorted(RAW.glob(f"*_{today}.json"))
check("6 raw API responses saved for today", len(raw_files) == 6,
      f"got {len(raw_files)}")
if len(raw_files) == 6:
    raw_rows = 0
    for f in raw_files:
        raw_rows += len(json.loads(f.read_text())["daily"]["time"])
    check("raw files hold 42 forecast days", raw_rows == 42,
          f"got {raw_rows}")
check("run summary exists and names the hottest city",
      SUMMARY.exists() and "Hottest day" in SUMMARY.read_text())
con.close()

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
