# Lesson 5 — Closing the Loop

**Module 5 · Deep dive · ~60–75 min**

## Before this lesson

**Lead-time warning, unlike every earlier lesson**: this lesson depends on a **Braze Data
Share** being provisioned into the sandbox's Snowflake account, which is a one-time setup Braze's
side has to action — it isn't something you enable yourself in the Braze dashboard. Request this
from CD's Braze account team (or whoever holds the sandbox relationship) at least a few days
before running this lesson, giving them the sandbox Snowflake account locator to share into. If
the Data Share isn't available in time, see the fallback note at the end of this lesson before
skipping the module entirely.

Also required: UC1's Canvas (Lesson 4) must have actually sent, and enough time must have passed
for engagement events to land in the share — Data Share tables update on Braze's own schedule,
not instantly.

## Learning objectives

By the end, the colleague should be able to:
1. Explain what a Braze Data Share is and how it differs from a regular Hightouch sync (data
   flows in the opposite direction — Braze pushes into Snowflake, nothing to configure in
   Hightouch for this leg).
2. Query engagement data landed via the share and join it back to the warehouse's own tables.
3. Build a refined segment from that join and close the loop with a follow-up send.

## 1. Accept the Data Share in Snowflake

Once Braze's side confirms the share is provisioned, in a Snowflake worksheet:

```sql
SHOW SHARES;
```

Look for an inbound share from Braze's account (name varies by how Braze's team configured it —
confirm the exact identifier with them rather than guessing). Then:

```sql
CREATE DATABASE IF NOT EXISTS BRAZE_SHARE_DB FROM SHARE <braze_account_locator>.<share_name>;
```

This materializes the share as a queryable database — no data is copied, it's a live view into
Braze's side.

📸 **Screenshot checkpoint**: `SHOW SHARES` output and the `CREATE DATABASE ... FROM SHARE` confirmation.

## 2. Find the engagement view and identify UC1's Canvas

1. Explore what the share contains:
   ```sql
   SHOW VIEWS IN DATABASE BRAZE_SHARE_DB;
   ```
   Look for an email-open or email-engagement view — naming follows Braze's own convention and
   varies by workspace (something like `USERS_MESSAGES_EMAIL_OPEN_SHARED_<workspace>_VW`).
   Confirm the exact name against what's actually there rather than assuming.
2. In the Braze dashboard, open the UC1 Canvas (`HT101 TW — UC1 Loyalty Upsell`) and find its
   API identifier (**Canvas details → API Identifier**, or the Canvas ID visible in the URL).
   You'll need this to filter the shared engagement view down to just this send.
3. Sanity-check row volume before building anything on top of it:
   ```sql
   SELECT COUNT(*)
   FROM BRAZE_SHARE_DB.SHARED.<engagement_view_name>
   WHERE campaign_id = '<UC1 canvas api id>'
   ```
   If this returns zero, stop — either not enough time has passed since the send, or the ID/view
   name is wrong. Don't build the Hightouch model on top of an empty check.

📸 **Screenshot checkpoint**: the Canvas API Identifier field, and the row-count query result above zero.

## 3. Build the Hightouch model joining engagement back to CUSTOMERS

1. **Models → Add model → SQL model**, source = the same Snowflake source from Lesson 1 (the
   share is queryable through the same connection, since it's just another database the role can
   see — confirm the role has `IMPORTED PRIVILEGES` on `BRAZE_SHARE_DB` if this errors):
   ```sql
   SELECT DISTINCT
     c.customer_id,
     TRUE AS ht101_tw_uc4_engaged_followup
   FROM DEMO_DB.HT101_TW.CUSTOMERS c
   JOIN BRAZE_SHARE_DB.SHARED.<engagement_view_name> eo
     ON eo.external_user_id = c.customer_id
   WHERE eo.campaign_id = '<UC1 canvas api id>'
   ```
   This is UC4 exactly as scoped in `../use-cases.md`: customers from UC1's send who opened —
   re-segmented for a follow-up, not a brand-new audience built from scratch.
2. Save as `TollWay - UC4 Engaged Followup`. Row count should be less than or equal to UC1's
   synced audience size from Lesson 4 (not everyone opens).

📸 **Screenshot checkpoint**: the model preview showing the row count.

## 4. Sync back to Braze and send the follow-up

1. **Syncs → Add sync**, source = `TollWay - UC4 Engaged Followup`, destination =
   `TollWay - Braze`, matched on `external_id = customer_id`, mapping
   `ht101_tw_uc4_engaged_followup` to a same-named Braze custom attribute.
2. Run the sync.
3. In Braze: **Segments → Create Segment**, filter Custom Attribute
   `ht101_tw_uc4_engaged_followup` is `true`. Save as `TollWay - Engaged Followup (UC4)`.
4. **Canvas → Create Canvas**, single-step email targeting that segment, mock content pitching a
   stronger Gold-tier offer (this is the "next-best-action" — a sharper message to people who've
   already shown interest, not a generic repeat of UC1). Name it
   `HT101 TW — UC4 Engaged Followup`. Launch.

📸 **Screenshot checkpoint**: the UC4 Canvas analytics view showing entries.

## 5. This is the loop, closed

Trace it end to end: a Snowflake table you loaded in Lesson 1 → a single customer view you built
in Lesson 2 → a segment synced to Braze in Lesson 4 → a real send → engagement data Braze pushed
back into that same Snowflake account → a refined segment built from it → a second, sharper send.
That round trip — warehouse to activation platform and back again, each pass smarter than the
last — is what a CDP actually buys a business, not just "send one campaign."

## If the Data Share isn't available in time

Braze also supports **Currents** (an event-stream export to cloud storage or a webhook) as an
alternative to Data Share — it requires an extra ingestion step (landing Currents' export
somewhere Snowflake can load from, e.g. an external stage over S3/GCS) rather than a direct
queryable database, which is more setup than this lesson assumes. If Data Share genuinely isn't
provisionable for the sandbox, treat this as a scoping conversation rather than a click-path
swap — the ingestion step needs designing properly, not squeezed into this lesson's step 1.

## Course complete

All five modules are now built for real, not just previewed. See `../../course/syllabus.md` for
the full module list and `../use-cases.md` for how each use case maps across them — worth a
second read now that all four have actually been built, to see how the pieces fit together.
