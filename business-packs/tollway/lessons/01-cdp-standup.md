# Lesson 1 — Stand Up the CDP

**Module 1 · Deep dive · ~60–75 min**

## Before this lesson

Data must already be loaded: `DEMO_DB.HT101_TW` schema exists with `CUSTOMERS` (1,000 rows),
`VEHICLES`, `GANTRIES` (48 rows), `TRIPS` (10,000 rows), `TOPUPS`, `SUPPORT_TICKETS` populated —
see `../mock-data/` and `../mock-data/load/load_snowflake.sql`. Run the row-count query from
`../dictionary/cheatsheet.md` in a Snowflake worksheet before this lesson starts, so you're not
debugging data-loading issues in front of the colleague.

## Learning objectives

By the end, the colleague should be able to:
1. Explain the difference between a Hightouch **source**, **model**, **sync**, and **destination**.
2. Connect a Snowflake source to Hightouch.
3. Build a raw SQL model and confirm it returns the expected row count.

## 1. Concept primer (10 min, no clicking yet)

Draw or reference the generic architecture diagram (`../../course/diagrams/architecture-overview.md`):

- **Source** = a read connection to a warehouse. Hightouch queries it; nothing is copied into
  Hightouch permanently.
- **Model** = a saved SQL query (or a table pointer) against a source. This is the reusable unit —
  everything downstream (segments, syncs) is built on a model, not on raw source tables directly.
- **Segment** = a filtered/audience view of a model, built either in SQL or in Customer Studio's
  visual builder (covered in Lesson 2).
- **Sync** = the job that moves a model's or segment's rows to a destination on a schedule or on demand.
- **Destination** = where the data lands — Braze, Salesforce, another warehouse, etc. (Module 3).

Today only covers source → model. Segments, syncs, and destinations are Module 3-4 territory —
this lesson stops at "can Hightouch see and query the data."

## 2. Connect the Snowflake source

1. In Hightouch, go to **Sources → Add source → Snowflake**.
2. Connection details:
   - Account: (the CD Hightouch sandbox's configured Snowflake account)
   - Warehouse: (whichever compute warehouse the sandbox uses)
   - Database: `DEMO_DB`
   - Schema: `HT101_TW`
   - Role / auth: use your own Snowflake login (you're already authenticated in Snowsight — Hightouch will ask for the same account, likely via a service user or OAuth depending on how the sandbox is configured)
3. Test the connection. Hightouch should list the 6 tables in `HT101_TW`.

📸 **Screenshot checkpoint**: the source connection success screen showing `DEMO_DB.HT101_TW` and its 6 tables listed.

## 3. Build the first raw model

1. **Models → Add model → SQL model**, source = the Snowflake source just created.
2. Paste the raw pass-through pattern from `../../course/recipes/hightouch-model-recipes.md`:
   ```sql
   SELECT * FROM DEMO_DB.HT101_TW.CUSTOMERS
   ```
   Fully qualified with database and schema — don't rely on a default schema context, since
   `DEMO_DB` has other schemas (e.g. `DEMO_DATA`) a bare table name could resolve into by mistake.
3. Run/preview. Check the row count reads **1,000**. If it doesn't match, stop and check the load step before continuing — don't build anything on top of a model with the wrong row count.
4. Save the model as `TollWay - Customers (raw)`.

📸 **Screenshot checkpoint**: the model preview pane showing the 1,000-row count and a sample of columns.

5. Repeat for `TRIPS` — save as `TollWay - Trips (raw)`, expect **10,000** rows.

📸 **Screenshot checkpoint**: the Trips raw model preview showing 10,000 rows.

## 4. Table model vs. SQL model (2 min discussion)

Hightouch also supports a "table" model type that just points at a table with no SQL. Recommend
SQL models even for a raw pass-through — it's one extra step now, but every model in this course
from here on is a SQL model, and consistency matters more than saving a click on day one.

## 5. Wrap-up (5 min)

- Recap: source connected, two raw models built, row counts verified against the source.
- Preview: Lesson 2 builds the actual single customer view on top of these raw models (plus
  `VEHICLES`) — two ways, Customer Studio and a hand-written SQL model — and compares them.
- If time is short, this is a natural stopping point — see `../../course/syllabus.md`'s pacing
  note on splitting into two half-sessions.
