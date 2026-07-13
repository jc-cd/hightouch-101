# Lesson 4 — Segments + Activation

**Module 4 · Deep dive · ~120–150 min (the longest lesson — consider splitting UC1 from UC2/UC3)**

## Before this lesson

Lessons 1–3 complete: single customer view built, Braze and Snowflake-writeback destinations
connected and proven. This lesson builds three real Braze activations — UC1, UC2, UC3 from
`../use-cases.md` — end to end: Hightouch segment → sync → Braze → Canvas → send. UC1 and
UC2/UC3 use two genuinely different Braze mechanisms, both real, both worth knowing.

## Learning objectives

By the end, the colleague should be able to:
1. Explain the two standard Hightouch→Braze reverse-ETL patterns: sync-as-custom-event with an
   Action-Based Canvas trigger (near-real-time, UC1), and sync-as-custom-attribute with a native
   Segment (batch/periodic, UC2/UC3) — and when each is the better choice.
2. Build a Hightouch segment and wire it to a Braze send using either pattern.
3. Compose two segments' logic together as an exclusion, rather than building a third campaign
   from scratch.

## 0. Concept primer — two ways a Hightouch segment becomes a Braze send (15 min)

Hightouch doesn't "send campaigns" — it moves data. The actual audience-targeting and message
sending happens inside Braze, on Braze's own native objects. There are two real, commonly-used
ways to bridge a Hightouch segment into a Braze send, and this lesson deliberately teaches both
rather than picking one:

**Pattern A — custom event + Action-Based Canvas trigger (UC1)**

1. A Hightouch model returns exactly the rows that qualify right now (e.g. UC1's loyalty
   candidates).
2. A sync fires a **custom event** for each qualifying row — not an attribute update. Braze's
   `/users/track` API accepts attributes, events, and purchases as genuinely distinct object
   types; Hightouch's Braze destination lets a sync target either.
3. A Canvas with an **Action-Based entry trigger** (trigger = that custom event) fires per-user
   the instant the event lands — no separate Braze Segment object is needed for entry at all.

This is near-real-time and closer to what a real "customer journey" trigger looks like — the
Canvas reacts to something happening, rather than periodically re-checking a static audience.

**Pattern B — custom attribute + native Segment (UC2, UC3)**

1. A Hightouch model returns exactly the rows that qualify, each with a boolean column set to
   `TRUE`.
2. A sync writes that boolean as a **custom attribute** onto the matching Braze profile.
3. A native Braze **Segment** filters on "custom attribute X is true" — a real object, built in
   the Braze dashboard, not something Hightouch creates for you.
4. A **Canvas** (or Campaign) with segment-entry targets that Segment and sends on a schedule or
   on demand.

This is the more common pattern for ongoing, audience-style campaigns — the segment is a stable,
inspectable object you can reuse across multiple sends, not a one-shot trigger.

Both are genuine patterns used in real Hightouch→Braze implementations, matched by
`external_id = customer_id` in either case. One operational note worth knowing now for Pattern B:
Hightouch sync modes control what happens to a profile that *used to* qualify but no longer does
on a later run ("add new only" vs. "add, update, and unset removed rows"). Use the full
add/update/unset mode for UC2/UC3's syncs — otherwise a customer who drops out of a segment keeps
a stale `true` attribute forever. Pattern A doesn't have this problem the same way: if a customer
no longer qualifies, the event simply never fires for them again — there's no stale flag to unset.

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

## 2. UC1 — Frequent-traveller loyalty upsell (Pattern A — event-triggered)

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
   exactly, since this is the same filter with the flag column added. The flag column's value
   doesn't actually matter for this pattern (every row already means "qualifies") — it's kept for
   consistency with UC2/UC3's models and because Hightouch still needs a column to hang the sync
   off, but you won't map it to a Braze attribute this time.
2. **Syncs → Add sync**, source = `TollWay - UC1 Loyalty Candidates`, destination =
   `TollWay - Braze`, match on `external_id = customer_id`.
3. **Sync behavior**: set the destination object type to **Track Event** (not "Update User
   Attributes" — check the sync configuration's object-type selector, it's a distinct mode).
   Event name: `ht101_tw_uc1_loyalty_qualified`. Every row the model returns fires this event
   once for that customer.
4. Run the sync. In Braze, **Users → search** a known qualifying customer ID and check their
   activity/event log for `ht101_tw_uc1_loyalty_qualified` — confirm the event actually landed
   before building the Canvas on top of it.

📸 **Screenshot checkpoint**: the UC1 sync's run history, and one profile's event log showing the fired event.

**Braze side:**

5. **Canvas → Create Canvas**. Entry: **Action-Based**, trigger: **Custom Event** →
   `ht101_tw_uc1_loyalty_qualified`. No Segment object needed for entry — the trigger *is* the
   audience definition. Step 1: Email message. Compose a simple mock subject/body (e.g. "You're
   close to Gold — take 3 more trips this month"). Name the Canvas
   `HT101 TW — UC1 Loyalty Upsell`.
6. Review, then launch. Since every profile's email is `@example.com`, nothing will actually
   deliver — safe to launch for real rather than leaving it in draft, which is the more honest
   test of the full pipeline.
7. Unlike a segment-entry send, launching an Action-Based Canvas makes it **stay active** — it
   keeps listening for the event indefinitely, not just once. Confirm the Canvas's entry count in
   its analytics view matches the number of customers who had the event fired for them in step 4.
   If you re-run the sync tomorrow, anyone still qualifying re-fires the event and re-enters —
   that's expected behavior for this pattern, not a bug.

📸 **Screenshot checkpoint**: the Canvas's Action-Based entry configuration, and the analytics view showing the entry count.

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
3. Re-run both syncs. Compare the new row counts against the pre-exclusion counts recorded
   earlier — they should drop by roughly the ~6% open-ticket-seeded cohort documented in
   `../dictionary/inconsistencies.md`.
4. Nothing else needs to change on either Canvas, but the reason differs by pattern: UC2's
   Segment-entry Canvas automatically reflects the new, smaller audience next time it evaluates
   entry, since it targets the segment, not a fixed list — confirm its estimated size dropped in
   Braze. UC1's Action-Based Canvas doesn't need a segment update at all; a customer who now has
   an open ticket simply stops appearing in the model, so the event never fires for them again on
   the next sync run — they naturally stop entering without anything being explicitly removed.

📸 **Screenshot checkpoint**: before/after row counts for both models, and UC2's Braze segment's updated estimated size.

## 5. Wrap-up (10 min)

- Recap: Braze profiles seeded, two real activations built and sent using two different
  patterns (UC1 event-triggered, UC2 segment-based), one exclusion composed into both without
  building a third campaign.
- Preview: Lesson 5 uses UC1's Canvas send specifically — its engagement data (opens/clicks)
  flows back into Snowflake via a Braze Data Share, gets re-queried in Hightouch, and becomes
  UC4's refined follow-up segment.
