# Hightouch Sync Recipes (generic)

## Segment → destination sync (Module 4 pattern)

1. Build a Customer Studio audience (or a SQL model that returns the target rows) — this is the
   segment definition.
2. Create a Sync: source = the segment/model, destination = the target platform (e.g. Braze).
3. Map fields — every attribute the destination platform needs to receive (email, first name,
   whatever the campaign/Canvas will personalize with) needs an explicit field mapping. Fields
   not mapped don't get sent, even if they exist on the model.
4. Set the sync schedule. For training, manual/on-demand triggering is fine — don't set up a
   recurring schedule against a shared sandbox unless intentionally testing that behavior.
5. Run the sync once, check the destination platform for the expected row count before building
   anything (a campaign, a Canvas) on top of it.

## Reverse-ETL sync (Module 5 pattern — write-back to the warehouse)

Same mechanics as above, but the destination is the warehouse itself — used to bring engagement
data (opens, clicks) that originated in the activation platform back into a queryable table.
Requires the activation platform to already be exporting that data somewhere Hightouch can read
it from (e.g. Braze Currents/Data Share landing in a warehouse-accessible location) — the sync
itself doesn't create that export, it just moves already-exported data around, or in some setups
reads directly from a data share without a separate sync at all.

## Exclusion / composition pattern (UC3-style)

Don't build a third full segment for "same audience, minus an exclusion list." Compose it:
either as a second condition in the same Customer Studio audience definition (an "AND NOT" or
"doesn't match" condition group), or as an anti-join in the underlying SQL model. The goal is
one sync feeding one send, with the exclusion logic baked into the segment definition rather
than post-processed afterward.
