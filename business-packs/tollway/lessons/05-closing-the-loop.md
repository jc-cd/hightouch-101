# Lesson 5 — Closing the Loop (roadmap stub)

**Module 5 · Roadmap overview only for Lesson 1 · ~15 min preview**

Not yet built out to full depth. This is the module the whole course architecture builds toward
— see `../dictionary/relationships.md`'s closing-the-loop diagram.

## What this module will cover

1. UC1's Braze Canvas send generates engagement events (opens, clicks).
2. Those events export via Braze Currents or Data Share (mechanism depends on what the sandbox's
   Braze plan supports — see `../../course/recipes/braze-canvas-recipes.md`) into a new Snowflake
   table (not yet created — this is genuinely new data, not something in the current 6-table
   dataset).
3. Hightouch re-queries that engagement table, joined back to the original UC1 segment logic, to
   build **UC4**: a refined re-engagement segment — e.g. "opened the loyalty email but didn't
   act — send a stronger offer" vs. "didn't open at all — try a different channel or time."
4. That refined segment syncs to Braze for a follow-up send.

## Roadmap talking points for Lesson 1

- "This is the payload the whole course has been building toward. Once we send something, Braze
  tells us who engaged. We bring that back into the warehouse and use it to make the *next*
  segment smarter than the first one — that's what 'closing the loop' means in a real CDP."

## To build before this becomes a full lesson

- Confirm the Currents/Data Share mechanism available in the sandbox (blocks the concrete click path).
- Design the exact schema of the new Snowflake engagement table once the export mechanism is confirmed.
- UC1 needs to have actually sent (Module 4 complete) before this module has real data to demonstrate against — this module cannot be taught in isolation.
