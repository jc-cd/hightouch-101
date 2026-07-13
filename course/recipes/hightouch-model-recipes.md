# Hightouch Model Recipes (generic)

Reusable SQL model patterns — true regardless of business pack. Business-pack lesson docs
reference these and fill in real table/column names.

## Raw SQL model (Module 1)

The simplest possible model — proves the source connection works and gives a baseline row count
to sanity-check every later model against.

```sql
SELECT *
FROM <schema>.<table>
```

Run it, check the row count matches what you expect from the generator's stderr output, move on.

## Single customer view via SQL model (Module 2, path B)

The "control/transparency" path — the colleague writes the join and aggregation by hand.

```sql
WITH trip_agg AS (
  SELECT customer_id, COUNT(*) AS trip_count, SUM(toll_amount) AS lifetime_spend, MAX(trip_datetime) AS last_trip_at
  FROM <trips_table>
  GROUP BY customer_id
),
vehicle_agg AS (
  SELECT customer_id, COUNT(*) AS vehicle_count
  FROM <vehicles_table>
  GROUP BY customer_id
)
SELECT
  c.*,
  COALESCE(t.trip_count, 0) AS trip_count,
  COALESCE(t.lifetime_spend, 0) AS lifetime_spend,
  t.last_trip_at,
  COALESCE(v.vehicle_count, 0) AS vehicle_count
FROM <customers_table> c
LEFT JOIN trip_agg t ON t.customer_id = c.customer_id
LEFT JOIN vehicle_agg v ON v.customer_id = c.customer_id
```

Anti-join / `LEFT JOIN ... IS NULL` over `NOT IN (SELECT ...)` for any exclusion logic — matches
house Snowflake convention and avoids Snowflake's `NOT IN` subquery-in-CTE support gap.

## Incremental / upsert model (later reference, not needed for Module 1-2)

When a model needs to detect changes rather than re-scan everything, the house pattern is a
`pk_hash` built from a deterministic column concatenation:

```sql
SELECT
  customer_id,
  MD5(CONCAT_WS('||', COALESCE(loyalty_tier, ''), COALESCE(account_status, ''), COALESCE(account_balance::VARCHAR, ''))) AS pk_hash,
  *
FROM <customers_table>
```

Always wrap each concatenated column in `COALESCE(..., '')` — pipe concatenation without it
collapses nulls and risks hash collisions across genuinely distinct rows.

## ROW_NUMBER tiebreaks

Any `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` ranking needs a deterministic final
tiebreak column (e.g. alphabetical on an ID), or ties produce non-deterministic results between
runs — a real incident cause on production Hightouch models, not a hypothetical.
