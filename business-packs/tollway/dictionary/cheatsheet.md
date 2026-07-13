# TollWay Diagnostic Cheatsheet

Queries reused across lessons — copy-paste starting points, not final answers. Every table
reference is fully qualified with `DEMO_DB.HT101_TW.` — don't rely on a prior `USE SCHEMA`
having been run, since `DEMO_DB` has other schemas (e.g. `DEMO_DATA`) a bare table name could
resolve into by mistake.

## Row counts (sanity check right after loading)

```sql
SELECT 'CUSTOMERS' AS table_name, COUNT(*) AS row_count FROM DEMO_DB.HT101_TW.CUSTOMERS
UNION ALL
SELECT 'VEHICLES', COUNT(*) FROM DEMO_DB.HT101_TW.VEHICLES
UNION ALL
SELECT 'GANTRIES', COUNT(*) FROM DEMO_DB.HT101_TW.GANTRIES
UNION ALL
SELECT 'TRIPS', COUNT(*) FROM DEMO_DB.HT101_TW.TRIPS
UNION ALL
SELECT 'TOPUPS', COUNT(*) FROM DEMO_DB.HT101_TW.TOPUPS
UNION ALL
SELECT 'SUPPORT_TICKETS', COUNT(*) FROM DEMO_DB.HT101_TW.SUPPORT_TICKETS
```

## Loyalty tier distribution (should be ~55/32/13 bronze/silver/gold)

```sql
SELECT loyalty_tier, COUNT(*) AS customers, ROUND(COUNT(*) / SUM(COUNT(*)) OVER () * 100, 1) AS pct
FROM DEMO_DB.HT101_TW.CUSTOMERS
GROUP BY loyalty_tier
ORDER BY customers DESC
```

## Zero-trip customers (should be ~12%)

```sql
SELECT COUNT(*) AS zero_trip_customers
FROM DEMO_DB.HT101_TW.CUSTOMERS c
LEFT JOIN DEMO_DB.HT101_TW.TRIPS t ON t.customer_id = c.customer_id
WHERE t.trip_id IS NULL
```

## A single customer's full profile (module 2 sanity check)

```sql
SELECT
  c.customer_id, c.first_name, c.last_name, c.loyalty_tier, c.account_balance,
  COUNT(DISTINCT v.vehicle_id) AS vehicle_count,
  COUNT(DISTINCT t.trip_id) AS trip_count,
  SUM(t.toll_amount) AS lifetime_toll_spend
FROM DEMO_DB.HT101_TW.CUSTOMERS c
LEFT JOIN DEMO_DB.HT101_TW.VEHICLES v ON v.customer_id = c.customer_id
LEFT JOIN DEMO_DB.HT101_TW.TRIPS t ON t.customer_id = c.customer_id
WHERE c.customer_id = 'ht101_tw_cust_000001'
GROUP BY c.customer_id, c.first_name, c.last_name, c.loyalty_tier, c.account_balance
```

## UC1 — frequent-traveller candidates (silver tier, high recent trip count)

```sql
SELECT c.customer_id, c.loyalty_tier, COUNT(t.trip_id) AS trips_last_90d
FROM DEMO_DB.HT101_TW.CUSTOMERS c
JOIN DEMO_DB.HT101_TW.TRIPS t ON t.customer_id = c.customer_id
WHERE c.loyalty_tier = 'silver'
  AND t.trip_datetime >= DATEADD(day, -90, CURRENT_DATE())
GROUP BY c.customer_id, c.loyalty_tier
HAVING COUNT(t.trip_id) >= 15
ORDER BY trips_last_90d DESC
```

## UC2 — low balance / auto top-up off, verify the seeded cohort shows up

```sql
SELECT c.customer_id, c.topup_mode, c.account_balance,
  MAX(CASE WHEN tu.status = 'success' THEN tu.topup_datetime END) AS last_successful_topup
FROM DEMO_DB.HT101_TW.CUSTOMERS c
JOIN DEMO_DB.HT101_TW.TOPUPS tu ON tu.customer_id = c.customer_id
WHERE c.topup_mode != 'auto'
GROUP BY c.customer_id, c.topup_mode, c.account_balance
HAVING last_successful_topup IS NULL OR last_successful_topup < DATEADD(day, -30, CURRENT_DATE())
ORDER BY last_successful_topup NULLS FIRST
```

## UC3 — open-complaint exclusion list (anti-join pattern)

```sql
SELECT c.customer_id
FROM DEMO_DB.HT101_TW.CUSTOMERS c
LEFT JOIN DEMO_DB.HT101_TW.SUPPORT_TICKETS st ON st.customer_id = c.customer_id AND st.status = 'open'
WHERE st.ticket_id IS NULL
```

Anti-join (`LEFT JOIN ... IS NULL`), not `NOT IN (SELECT ...)` — matches the house Snowflake
convention, and avoids the `NOT IN` subquery-in-CTE support gap Snowflake has in some contexts.

## Readable trip detail (join to GANTRIES for road names instead of IDs)

```sql
SELECT t.trip_id, t.customer_id, g.road_name, g.locality, g.state, t.trip_datetime, t.toll_amount
FROM DEMO_DB.HT101_TW.TRIPS t
JOIN DEMO_DB.HT101_TW.GANTRIES g ON g.gantry_id = t.gantry_id
ORDER BY t.trip_datetime DESC
LIMIT 20
```
