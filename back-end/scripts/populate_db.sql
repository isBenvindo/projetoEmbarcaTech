-- back-end/scripts/populate_db.sql
-- This script cleans and populates the 'pizza_counts' table with realistic sample data for the past year.
-- It simulates weekly patterns (peak on Fridays, lulls on weekends) and avoids a lunch break hour.
-- Use a transaction to ensure the entire operation succeeds or fails together.
BEGIN;
-- Clear the table to ensure idempotency on repeated runs.
TRUNCATE TABLE pizza_counts RESTART IDENTITY;
-- Use Common Table Expressions (CTEs) to build the data in a readable, step-by-step pipeline.
WITH
-- 1. Generate a series of all days in the past year.
days AS (
SELECT generate_series(
(CURRENT_DATE - INTERVAL '365 days'),
CURRENT_DATE,
INTERVAL '1 day'
)::date AS day
),
-- 2. Define the number of records to generate for each day based on the day of the week.
daily_config AS (
SELECT
day,
-- EXTRACT(ISODOW FROM day) -> 1=Mon, 5=Fri, 6=Sat, 7=Sun
CASE
WHEN EXTRACT(ISODOW FROM day) = 5 -- Friday (peak)
THEN floor(random() * (300 - 180 + 1) + 180)::int
WHEN EXTRACT(ISODOW FROM day) IN (6, 7) -- Weekend (lull)
THEN floor(random() * (15 - 0 + 1) + 0)::int
ELSE -- Normal weekdays
floor(random() * (220 - 120 + 1) + 120)::int
END AS num_records
FROM days
),
-- 3. Expand the rows: for each day, create N rows, where N is the 'num_records' for that day.
expanded_events AS (
SELECT day
FROM daily_config
CROSS JOIN LATERAL generate_series(1, num_records)
),
-- 4. For each expanded row, generate a realistic timestamp, avoiding the lunch hour (12:00-12:59).
final_timestamps AS (
SELECT
(day +
-- Randomly choose between a morning shift (0) and an afternoon shift (1)
CASE WHEN floor(random() * 2)::int = 0
-- Morning: 08:00:00 to 11:59:59
THEN make_interval(hours := 8 + floor(random() * 4)::int,
mins := floor(random() * 60)::int,
secs := floor(random() * 60)::int)
-- Afternoon: 13:00:00 to 16:59:59
ELSE make_interval(hours := 13 + floor(random() * 4)::int,
mins := floor(random() * 60)::int,
secs := floor(random() * 60)::int)
END
)::timestamptz AS ts
FROM expanded_events
)
-- 5. Insert all generated timestamps into the final table.
INSERT INTO pizza_counts (timestamp)
SELECT ts FROM final_timestamps;
-- Commit the transaction to make the changes permanent.
COMMIT;