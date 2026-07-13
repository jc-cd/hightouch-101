# Lesson 3 — Destinations

**Module 3 · Deep dive · ~45–60 min**

## Before this lesson

Lessons 1–2 complete: Snowflake source connected, raw models for `CUSTOMERS`/`VEHICLES`/`TRIPS`
built, and a single customer view built both ways (Customer Studio + SQL model). This lesson
wires up the two destinations everything from Lesson 4 onward depends on: Braze (where segments
get activated) and a Snowflake reverse-ETL destination (where Braze engagement data eventually
writes back to, in Lesson 5).

## Learning objectives

By the end, the colleague should be able to:
1. Connect Braze as a Hightouch destination and understand what a destination connection can and can't do on its own (it moves data — it doesn't decide who receives what; that's Braze's job once the data lands).
2. Connect a Snowflake reverse-ETL destination and understand why it's a second connection, not the same one used for the source.
3. Explain the field-mapping step, since every later sync in this course depends on getting it right.

## 1. Add Braze as a destination

1. In Hightouch, go to **Destinations → Add destination → Braze**.
2. Connection details:
   - REST endpoint: the CD Braze sandbox workspace's REST API URL (e.g. `https://rest.iad-01.braze.com` — the exact cluster subdomain depends on which Braze instance the sandbox lives on; check the Braze dashboard's **Settings → APIs and Identifiers** page if unsure).
   - REST API key: a key from the sandbox workspace with `users.track` permission at minimum (that's the permission Hightouch needs to write custom attributes onto profiles — confirm the key has it before moving on, since a key without it will fail silently on some sync types and loudly on others).
3. Test the connection. Hightouch should confirm it can reach the Braze workspace.
4. Save the destination as `TollWay - Braze`.

📸 **Screenshot checkpoint**: the Braze destination connection success screen.

## 2. Add a Snowflake reverse-ETL destination

This is a **second** connection object even though it points at the same Snowflake account as
the source from Lesson 1 — Hightouch treats "read from a warehouse" (source) and "write to a
warehouse" (destination) as separate connections, each with their own credentials/role scope.
Reusing the source connection object for writes is not how Hightouch models this, and trying to
force it will just confuse the sync-builder UI later.

1. **Destinations → Add destination → Snowflake**.
2. Same account/warehouse as the Lesson 1 source, but confirm the role being used has `INSERT`/
   `CREATE TABLE` grants on `DEMO_DB.HT101_TW` — the read-only role from Lesson 1 may not have
   write access, and that's a deliberate Snowflake permissions boundary, not a bug to work around.
3. Test the connection.
4. Save the destination as `TollWay - Snowflake Writeback`.

📸 **Screenshot checkpoint**: the Snowflake reverse-ETL destination connection success screen.

## 3. Prove the write-back path with a throwaway sync

Don't wait until Lesson 5 to find out the writeback destination doesn't actually work — prove it
now with the smallest possible sync, using the Trips raw model from Lesson 1.

1. **Syncs → Add sync**, source model = `TollWay - Trips (raw)`, destination =
   `TollWay - Snowflake Writeback`.
2. Target table: let Hightouch create a new table, name it `HT101_TW_WRITEBACK_TEST`.
3. Field mapping: map just `trip_id` and `toll_amount` — a full-column mapping isn't the point
   here, proving the connection can create and write a table is.
4. Run the sync once. Confirm in a Snowflake worksheet:
   ```sql
   SELECT COUNT(*) FROM DEMO_DB.HT101_TW.HT101_TW_WRITEBACK_TEST
   ```
   Row count should match the Trips model's row count (10,000 with the default generator seed).
5. Once confirmed, either drop the test table or leave it — it doesn't collide with anything and
   the environment's own reset process will clear it along with everything else.

📸 **Screenshot checkpoint**: the sync run history showing a successful write, and the row-count query result.

## 4. Field mapping — why this step matters for everything downstream

Every sync — this test one, and every real one in Lessons 4–5 — only sends the fields explicitly
mapped in that sync's configuration. A model or segment can carry twenty columns; if a sync maps
three of them, the destination receives three. This trips people up specifically going into
Lesson 4, where the whole mechanic is "sync writes one boolean attribute onto the Braze profile"
— if that one field isn't mapped, the sync will run, report success, and silently do nothing
useful. Get in the habit of checking the field mapping panel every time, not just the destination
and the row count.

## 5. Wrap-up (5 min)

- Recap: Braze destination connected, Snowflake reverse-ETL destination connected and proven
  with a real write, field-mapping mechanics understood.
- Preview: Lesson 4 builds the first real segment (UC1) and syncs it to Braze as a custom
  attribute, then builds the Braze-side Segment, Canvas, and send on top of it.
