# TollWay Use Cases

Four use cases, mapped across Modules 1–5. Cut down from six candidates during planning —
**onboarding/welcome** (better suited to a later Canvas-triggers lesson, not a segment/sync
exercise) and **churn win-back** (overlaps mechanically with UC2 for a usage-based, non-
subscription business) are good additions for a later session, not needed for v1.

## UC1 — Frequent-traveller loyalty upsell (the hero use case)

**Who**: Silver-tier customers with high trip volume in the trailing 90 days — candidates for a Gold-tier nudge.

**Data**: `CUSTOMERS.loyalty_tier = 'silver'` joined to a `TRIPS` count/recency aggregate.

**Modules**: 4 (segment → sync → Braze campaign, the first full send), 5 (this send's engagement is what gets read back in the closing-the-loop exercise).

**Why it's the first one taught**: single-table-plus-aggregate filter — the simplest possible "real" segment, and the happy path for a first full segment→sync→send walkthrough.

## UC2 — Low-balance / auto-top-up-off nudge

**Who**: customers not on auto top-up, with no successful recharge in the trailing 30 days.

**Data**: `CUSTOMERS.topup_mode != 'auto'` joined to `TOPUPS` (a table not yet touched in Modules 1-2).

**Modules**: 4 (segment → sync → Braze campaign).

**Why it's second**: introduces a second table into segment logic — the colleague has to combine two tables, not just filter one.

## UC3 — Open-complaint suppression

**Who**: exclude anyone from UC1 or UC2's send list who currently has an open support ticket.

**Data**: `SUPPORT_TICKETS.status = 'open'`, anti-joined onto UC1/UC2.

**Modules**: 4 (exclusion logic layered onto UC1/UC2, not a standalone third send).

**Why it's structured as an exclusion, not a third campaign**: teaches segment composition as a
concept — real segmentation is rarely "one filter, one send"; it's usually "this audience, minus
this exclusion list." Keeps Module 4 to two actual sends, not three, which keeps the roadmap
overview digestible.

## UC4 — Closing the loop

**Who**: customers from UC1's send who opened or clicked, re-segmented for a next-best-action follow-up.

**Data**: Braze Canvas on UC1's send → Currents/Data Share → a new Snowflake engagement table (built in Module 5, doesn't exist yet) → re-queried in Hightouch → refined segment.

**Modules**: 5 (this is Module 5's entire payload).

**Why it's last**: it depends on UC1 having already sent and generated real engagement data — sequencing is a hard dependency, not a stylistic choice. This is also the one use case that visually justifies the whole course architecture (see `dictionary/relationships.md`'s closing-the-loop diagram).
