-- Mini #7 — ETL target schema (SQLite).
-- One row per city per day. run_date stamps the fetch so re-runs
-- (new forecasts) never silently mix with old ones; this load keeps
-- one run only (the loader rebuilds the DB), which the checks prove.

CREATE TABLE dim_city (
    city      TEXT PRIMARY KEY,
    latitude  REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE fact_forecast (
    city           TEXT NOT NULL REFERENCES dim_city(city),
    forecast_date  TEXT NOT NULL,
    temp_max_c     REAL NOT NULL,
    temp_min_c     REAL NOT NULL,
    precip_mm      REAL NOT NULL,
    wind_max_kmh   REAL NOT NULL,
    run_date       TEXT NOT NULL,
    PRIMARY KEY (city, forecast_date)
);
