# Lesson 2 — Single Customer View

**Module 2 · Deep dive · ~75–90 min**

## Before this lesson

Lesson 1 complete: Snowflake source connected, raw `Customers` and `Trips` SQL models built and
verified. This lesson adds a raw `Vehicles` model, then builds the same single customer view two
ways.

## Learning objectives

By the end, the colleague should be able to:
1. Build a unified customer profile using Hightouch **Customer Studio** identity resolution.
2. Build the same profile using a **hand-written SQL model**.
3. Explain when each approach is the better choice.

## 1. Add the Vehicles raw model (5 min)

Same pattern as Lesson 1: **Models → Add model → SQL model**,
`SELECT * FROM DEMO_DB.HT101_TW.VEHICLES`, save as `TollWay - Vehicles (raw)`. Expected row
count is 1,407 with the default seed (varies if regenerated with a different `--seed`) — check
against the count from `../dictionary/cheatsheet.md`'s row-count query, not a fixed number.

## 2. Path A — Customer Studio identity resolution (30–35 min)

1. Go to **Customer Studio → Identity Resolution** (or equivalent setup wizard, naming varies by
   Hightouch version).
2. Set the **primary source** to `TollWay - Customers (raw)`, keyed on `customer_id`. This is the
   spine — every other source joins onto this identity.
3. Add **related sources**:
   - `TollWay - Vehicles (raw)`, joined on `customer_id`.
   - `TollWay - Trips (raw)`, joined on `customer_id`.
4. Let Hightouch build the **Unified Profile schema**. Review what it inferred — check whether it
   surfaced derived counts (vehicle count, trip count) automatically or whether those need to be
   added as calculated traits.
5. Open one customer's unified profile (pick `ht101_tw_cust_000001` or any known ID) and note
   what it shows: identity fields from `CUSTOMERS`, a list/count of related `VEHICLES` rows, a
   list/count of related `TRIPS` rows.

📸 **Screenshot checkpoint**: the Identity Resolution source graph (Customers as primary, Vehicles and Trips as related sources).

📸 **Screenshot checkpoint**: one customer's Unified Profile view.

## 3. Path B — hand-written SQL model (25–30 min)

1. **Models → Add model → SQL model**, source = Snowflake source.
2. Use the single-customer-view pattern from `../../course/recipes/hightouch-model-recipes.md`
   (aggregate `TRIPS` and `VEHICLES` into CTEs, left join onto `CUSTOMERS`):
   ```sql
   WITH trip_agg AS (
     SELECT customer_id, COUNT(*) AS trip_count, SUM(toll_amount) AS lifetime_spend, MAX(trip_datetime) AS last_trip_at
     FROM DEMO_DB.HT101_TW.TRIPS
     GROUP BY customer_id
   ),
   vehicle_agg AS (
     SELECT customer_id, COUNT(*) AS vehicle_count
     FROM DEMO_DB.HT101_TW.VEHICLES
     GROUP BY customer_id
   )
   SELECT
     c.*,
     COALESCE(t.trip_count, 0) AS trip_count,
     COALESCE(t.lifetime_spend, 0) AS lifetime_spend,
     t.last_trip_at,
     COALESCE(v.vehicle_count, 0) AS vehicle_count
   FROM DEMO_DB.HT101_TW.CUSTOMERS c
   LEFT JOIN trip_agg t ON t.customer_id = c.customer_id
   LEFT JOIN vehicle_agg v ON v.customer_id = c.customer_id
   ```
   Fully qualified with database and schema — `DEMO_DB` has other schemas (e.g. `DEMO_DATA`) a
   bare table name could resolve into by mistake.
3. Run it. Save as `TollWay - Single Customer View (SQL)`.
4. Look up the same customer (`ht101_tw_cust_000001`) in this model's output and compare the
   `trip_count`/`vehicle_count`/`lifetime_spend` numbers against what Customer Studio showed in
   Path A, and against the ground-truth query in `../dictionary/cheatsheet.md` ("A single
   customer's full profile"). All three should agree.

📸 **Screenshot checkpoint**: the SQL model's preview for `ht101_tw_cust_000001`, side by side (mentally or in two browser tabs) with the Customer Studio profile from Path A.

## 4. Compare the two paths (10 min discussion)

| | Customer Studio | SQL model |
|---|---|---|
| Speed to build | Faster — wizard-driven, no SQL to write | Slower — write and debug the join/aggregation yourself |
| Governance | Built-in guardrails, consistent unified schema across the workspace | No guardrails — whatever you write is what you get |
| Transparency | Some logic is implicit (how it resolves/merges is partly abstracted) | Fully transparent — every join and aggregation is visible in the SQL |
| Best for | Fast identity resolution across many sources, especially when non-technical teammates need to browse profiles | Precise control over a specific derived metric, or when the exact aggregation logic needs to be auditable |

Neither path is "the right one" — real Hightouch usage mixes both. Segments in Module 4 can be
built off either the Customer Studio unified profile or a SQL model; the choice depends on
whether the segment's condition needs Customer Studio's visual builder or a calculation that's
easier to express directly in SQL.

## 5. Wrap-up + roadmap preview (10 min)

- Recap: two working single-customer-view builds, cross-checked against a ground-truth query.
- Preview modules 3–5 at roadmap level (see `../../course/syllabus.md` and
  `../../course/diagrams/course-flow.md`):
  - Module 3: wire up Braze and a Snowflake write-back destination.
  - Module 4: build the loyalty-upsell segment (UC1) and send it to Braze; then the low-balance
    (UC2) and complaint-suppression (UC3) use cases.
  - Module 5: close the loop — Braze engagement data flows back to Snowflake, gets re-queried in
    Hightouch, builds a smarter follow-up segment.
- These become full lesson docs in later sessions — see the roadmap stubs in
  `03-destinations.md`, `04-segments-and-activation.md`, `05-closing-the-loop.md`.
