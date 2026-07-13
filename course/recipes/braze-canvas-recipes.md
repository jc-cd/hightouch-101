# Braze Canvas + Currents Recipes (generic)

## Attribute+Segment vs. Event+Action-Trigger — which to reach for

Two real patterns bridge a Hightouch segment into a Braze send, matched by
`external_id = customer_id` in both cases:

- **Event + Action-Based trigger**: the sync fires a Braze **custom event** (not an attribute
  update) via `/users/track`; a Canvas with an Action-Based entry trigger keyed to that event
  fires per-user the instant it lands. No Braze Segment object needed for entry. Near-real-time,
  good for "something just happened, react now" sends. Once launched, the Canvas stays active and
  re-triggers every time the event fires again — there's no stale-flag problem, since a customer
  who stops qualifying just stops generating the event.
- **Attribute + native Segment**: the sync writes a boolean **custom attribute**; a Braze
  Segment filters on it; a Canvas or Campaign with segment-entry targets the Segment. Batch/
  periodic — the more common pattern for ongoing, audience-style campaigns, since the Segment is
  a stable, reusable, inspectable object. Needs the sync's full add/update/unset mode, or a
  customer who drops out keeps a stale `true` attribute forever.

Neither is "more correct" — pick based on whether the send is reacting to something happening
(event) or targeting a standing audience (attribute+segment). This course teaches both: see
`../../business-packs/tollway/lessons/04-segments-and-activation.md` for a worked example of each.

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
