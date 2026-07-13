# Braze Canvas + Currents Recipes (generic)

## Single-send Canvas (Module 4 pattern)

For a first exercise, a Canvas with exactly one step (send email) targeting the synced segment
is enough to prove the segment→sync→Braze pipeline works end to end. Don't reach for multi-step
Canvas logic (delays, branches, multiple channels) until the single-step version has been
verified to actually deliver to the expected audience size.

## Currents / Data Share → warehouse write-back (Module 5 pattern)

Braze Currents (event stream export) or Data Share (direct warehouse share, where available) is
how engagement events — opens, clicks, Canvas entries/exits — leave Braze and become
warehouse-queryable again. This is the mechanism, not a specific implementation: which one is
available depends on the sandbox's Braze plan and whether a Snowflake Data Share connection has
already been set up for the sandbox account. Confirm which path the sandbox supports before
building Module 5's lesson content in detail.

## Teardown dependency ordering (why order matters)

A Canvas references a segment (as its target audience) and, if Currents/Data Share is
configured, an export destination. Braze will not let a segment be deleted while a live Canvas
still targets it — so Canvases (and Campaigns, same mechanic) must be deleted or archived
*before* the segments they reference. This is the reasoning behind the reset checklist's
ordering in `../reset/hightouch-braze-checklist-template.md` — it's not an arbitrary sequence,
it's what the platform's own referential constraints require.
