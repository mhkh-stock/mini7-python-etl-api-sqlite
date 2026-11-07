-- Mini #7 — analysis questions over the loaded forecast.
-- Run: sqlite3 data/weather.db < sql/analysis.sql

-- 1. Hottest city-day in the window.
SELECT city, forecast_date, temp_max_c
FROM fact_forecast
ORDER BY temp_max_c DESC LIMIT 1;

-- 2. Wettest week by city (total precipitation).
SELECT city, ROUND(SUM(precip_mm), 1) AS total_precip_mm
FROM fact_forecast GROUP BY city ORDER BY 2 DESC;

-- 3. Biggest day-night temperature swing.
SELECT city, forecast_date,
       ROUND(temp_max_c - temp_min_c, 1) AS swing_c
FROM fact_forecast ORDER BY swing_c DESC LIMIT 5;

-- 4. Average max temperature by city (the week's warmth ranking).
SELECT city, ROUND(AVG(temp_max_c), 1) AS avg_max_c,
       ROUND(AVG(temp_min_c), 1) AS avg_min_c
FROM fact_forecast GROUP BY city ORDER BY avg_max_c DESC;

-- 5. Rainy days per city (precipitation > 0). Every city is listed,
--    even one with zero rainy days — a city must show 0, not vanish.
SELECT city, SUM(CASE WHEN precip_mm > 0 THEN 1 ELSE 0 END) AS rainy_days
FROM fact_forecast GROUP BY city ORDER BY rainy_days DESC, city;
