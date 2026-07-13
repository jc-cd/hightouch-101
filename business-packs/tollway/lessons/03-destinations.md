# Lesson 3 — Destinations (roadmap stub)

**Module 3 · Roadmap overview only for Lesson 1 · ~15 min preview**

Not yet built out to full depth — this is what to say in the roadmap preview, not a click path.

## What this module will cover

- Add **Braze** as a destination (API key/endpoint for the CD Braze sandbox workspace).
- Add a **Snowflake reverse-ETL destination** pointing back at `DEMO_DB.HT101_TW` — this is the
  write-back path Module 5 depends on, so it needs to exist before Module 5 can be taught in
  full.
- Explain field mapping: a destination only receives fields explicitly mapped in a sync (covered
  properly in Module 4), not everything a model returns.

## Roadmap talking points for Lesson 1

- "Once we have a single customer view, we need somewhere to send it — that's a destination.
  We'll set up Braze (to send campaigns) and a way to write data back into Snowflake (so
  engagement data has somewhere to land later)."
- Don't demo this live in Lesson 1 — it's a short, mostly-configuration module with no
  interesting decisions to walk through yet without a segment to sync.

## To build before this becomes a full lesson

- Confirm the CD Braze sandbox workspace details (API key/endpoint) to reference here.
- Confirm whether the sandbox's Braze plan supports Currents or Data Share (needed for Module 5) — see `../../course/recipes/braze-canvas-recipes.md`.
