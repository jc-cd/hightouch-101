# Lesson 4 — Segments + Activation

**Module 4 · Deep dive · ~120–150 min (the longest lesson — consider splitting UC1 from UC2/UC3)**

## Before this lesson

Lessons 1–3 complete: single customer view built, Braze and Snowflake-writeback destinations
connected and proven. This lesson builds three real Braze activations — UC1, UC2, UC3 from
`../use-cases.md` — end to end: Hightouch segment → sync → Braze Segment → Canvas → send.

## Learning objectives

By the end, the colleague should be able to:
1. Explain the standard Hightouch→Braze reverse-ETL pattern: a sync writes a boolean custom
   attribute onto the Braze profile; Braze's own native Segment then filters on that attribute.
2. Build a Hightouch segment, sync it as a flag, and build the matching Braze Segment + Canvas.
3. Compose two segments' logic together as an exclusion, rather than building a third campaign
   from scratch.

## 0. Concept primer — how a Hightouch segment becomes a Braze send (10 min)

Hightouch doesn't "send campaigns" — it moves data. The actual audience-targeting and message
sending happens inside Braze, on Braze's own native Segment/Canvas objects. The bridge between
the two is a **synced custom attribute**:

1. A Hightouch model/segment returns exactly the rows that qualify for something (e.g. UC1's
   loyalty candidates), each with a boolean column set to `TRUE`.
2. A sync writes that boolean as a **custom attribute** onto the matching Braze profile, matched
   by `external_id = customer_id`.
3. In Braze, a native **Segment** filters on "custom attribute X is true" — this is a real Braze
   object, built in the Braze dashboard, not something Hightouch creates for you.
4. A **Canvas** (or Campaign) targets that Braze Segment and actually sends.

This is the same pattern used in real Hightouch→Braze implementations — it's not a
training-only simplification. One operational note worth knowing now: Hightouch sync modes
control what happens to a profile that *used to* qualify but no longer does on a later run
("add new only" vs. "add, update, and unset removed rows"). Use the full add/update/unset mode
for every sync in this lesson — otherwise a customer who drops out of a segment keeps a stale
`true` attribute forever.

## 1. Seed the Braze profiles first

None of the three use cases below will work if the underlying Braze profiles don't exist yet.
Do this once, before UC1.

1. **Syncs → Add sync**, source model = `TollWay - Single Customer View (SQL)` (from Lesson 2),
   destination = `TollWay - Braze`.
2. Match on `external_id = customer_id`.
3. Field mapping — map at minimum:
   - `email` → `email`
   - `first_name` → `first_name`
   - `last_name` → `last_name`
   - `marketing_email_subscribe` → `email_subscribe` (Braze's standard subscription field —
     values `subscribed`/`unsubscribed`/`opted_in` map directly, no transformation needed)
   - `loyalty_tier` → a custom attribute `ht101_tw_loyalty_tier`
4. Run the sync. In the Braze dashboard, **Users → search** any known ID (e.g.
   `ht101_tw_cust_000001`) and confirm the profile exists with the mapped fields populated.

📸 **Screenshot checkpoint**: the seed sync's run history showing ~1,000 profiles created/updated, and one profile's detail view in Braze.

## 2. UC1 — Frequent-traveller loyalty upsell

**Hightouch side:**

1. **Models → Add model → SQL model**:
   ```sql
   SELECT
     c.customer_id,
     TRUE AS ht101_tw_uc1_loyalty_candidate
   FROM DEMO_DB.HT101_TW.CUSTOMERS c
   JOIN DEMO_DB.HT101_TW.TRIPS t ON t.customer_id = c.customer_id
   WHERE c.loyalty_tier = 'silver'
     AND t.trip_datetime >= DATEADD(day, -90, CURRENT_DATE())
   GROUP BY c.customer_id
   HAVING COUNT(t.trip_id) >= 15
   ```
   Save as `TollWay - UC1 Loyalty Candidates`. Check the row count against the cheatsheet query
   in `../dictionary/cheatsheet.md` ("UC1 — frequent-traveller candidates") — they should match
   exactly, since this is the same filter with the flag column added.
2. **Syncs → Add sync**, source = `TollWay - UC1 Loyalty Candidates`, destination =
   `TollWay - Braze`, match on `external_id = customer_id`.
3. Field mapping: map `ht101_tw_uc1_loyalty_candidate` → a Braze custom attribute of the same
   name. This is the only field this sync needs to send — the identity fields were already
   seeded in step 1.
4. Run the sync. Confirm the row count matches the model's row count.

📸 **Screenshot checkpoint**: the UC1 sync's run history and row count.

**Braze side:**

5. **Audience → Segments → Create Segment**. Filter: Custom Attribute
   `ht101_tw_uc1_loyalty_candidate` **is** `true`. Save as `TollWay - Loyalty Upsell (UC1)`.
6. Check the segment's estimated size in Braze — it should match the Hightouch sync's row count.
   If it doesn't, stop and check the field mapping before building anything on top of it.
7. **Canvas → Create Canvas**. Single-step, entry: segment entry targeting
   `TollWay - Loyalty Upsell (UC1)`. Step 1: Email message. Compose a simple mock subject/body
   (e.g. "You're close to Gold — take 3 more trips this month"). Name the Canvas
   `HT101 TW — UC1 Loyalty Upsell`.
8. Review, then launch. Since every profile's email is `@example.com`, nothing will actually
   deliver — safe to launch for real rather than leaving it in draft, which is the more honest
   test of the full pipeline.
9. Confirm the Canvas's entry count in its analytics view matches the segment size.

📸 **Screenshot checkpoint**: the Canvas analytics view showing the entry count.

## 3. UC2 — Low-balance / auto-top-up-off nudge

Same pattern as UC1, faster now that the mechanic is familiar. This is the one that introduces
`TOPUPS` — a table not yet touched by any Hightouch model in this course.

**Hightouch side:**

1. New SQL model:
   ```sql
   SELECT
     c.customer_id,
     TRUE AS ht101_tw_uc2_low_balance_candidate
   FROM DEMO_DB.HT101_TW.CUSTOMERS c
   JOIN DEMO_DB.HT101_TW.TOPUPS tu ON tu.customer_id = c.customer_id
   WHERE c.topup_mode != 'auto'
   GROUP BY c.customer_id
   HAVING MAX(CASE WHEN tu.status = 'success' THEN tu.topup_datetime END) IS NULL
      OR MAX(CASE WHEN tu.status = 'success' THEN tu.topup_datetime END) < DATEADD(day, -30, CURRENT_DATE())
   ```
   Save as `TollWay - UC2 Low Balance Candidates`.
2. Sync to `TollWay - Braze`, matched on `external_id = customer_id`, mapping
   `ht101_tw_uc2_low_balance_candidate` to a same-named Braze custom attribute.

**Braze side:**

3. Segment: Custom Attribute `ht101_tw_uc2_low_balance_candidate` is `true`. Save as
   `TollWay - Low Balance Nudge (UC2)`.
4. Canvas: single-step email, named `HT101 TW — UC2 Low Balance Nudge`, mock content prompting
   the customer to turn on auto top-up. Launch.

📸 **Screenshot checkpoint**: UC2's sync run history and Canvas analytics, same as UC1.

## 4. UC3 — Open-complaint suppression (not a third campaign)

This one doesn't get its own Canvas. It modifies UC1 and UC2's *segment definitions* to exclude
anyone with a currently open support ticket — the point is learning to compose an exclusion into
an existing audience, which is what real-world segmentation looks like far more often than a
clean single filter.

1. Edit `TollWay - UC1 Loyalty Candidates`, adding an anti-join:
   ```sql
   SELECT
     c.customer_id,
     TRUE AS ht101_tw_uc1_loyalty_candidate
   FROM DEMO_DB.HT101_TW.CUSTOMERS c
   JOIN DEMO_DB.HT101_TW.TRIPS t ON t.customer_id = c.customer_id
   LEFT JOIN DEMO_DB.HT101_TW.SUPPORT_TICKETS st
     ON st.customer_id = c.customer_id AND st.status = 'open'
   WHERE c.loyalty_tier = 'silver'
     AND t.trip_datetime >= DATEADD(day, -90, CURRENT_DATE())
   GROUP BY c.customer_id
   HAVING COUNT(t.trip_id) >= 15 AND MAX(st.ticket_id) IS NULL
   ```
   The `LEFT JOIN ... IS NULL` anti-join pattern, not `NOT IN (SELECT ...)` — same house
   convention as the cheatsheet's UC3 query. `MAX(st.ticket_id) IS NULL` in the `HAVING` clause
   is what actually excludes a customer: if any open ticket joined in, that column is non-null
   for that customer and the row gets dropped.
2. Repeat the same anti-join addition on `TollWay - UC2 Low Balance Candidates`.
3. Re-run both syncs. Compare the new row counts against the pre-exclusion counts recorded in
   steps 2–3 above — they should drop by roughly the ~6% open-ticket-seeded cohort documented in
   `../dictionary/inconsistencies.md`.
4. Back in Braze, confirm both segments' estimated sizes dropped by a matching amount. Nothing
   else needs to change — the Canvases built in UC1/UC2 automatically reflect the new, smaller
   audience the next time they evaluate entry, since they target the segment, not a fixed list.

📸 **Screenshot checkpoint**: before/after row counts for both models, and the two Braze segments' updated estimated sizes.

## 5. Wrap-up (10 min)

- Recap: Braze profiles seeded, two real segment→sync→Canvas activations built and sent, one
  exclusion composed into both without building a third campaign.
- Preview: Lesson 5 uses UC1's Canvas send specifically — its engagement data (opens/clicks)
  flows back into Snowflake via a Braze Data Share, gets re-queried in Hightouch, and becomes
  UC4's refined follow-up segment.
