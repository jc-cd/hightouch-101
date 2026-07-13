# Lesson 4 — Segments + Activation (roadmap stub)

**Module 4 · Roadmap overview only for Lesson 1 · ~15 min preview**

Not yet built out to full depth. Full use-case detail lives in `../use-cases.md` (UC1-UC3) —
this stub is the talking-point version for Lesson 1's roadmap preview.

## What this module will cover

1. **UC1 — Frequent-traveller loyalty upsell**: build a segment (Silver tier, high recent trip
   count), sync to Braze, send a single-step Canvas email. The "happy path" first full
   segment→sync→send walkthrough.
2. **UC2 — Low-balance / auto-top-up-off nudge**: a second segment introducing the `TOPUPS`
   table for the first time.
3. **UC3 — Open-complaint suppression**: not a third campaign — an exclusion condition layered
   onto UC1/UC2's segment definitions, using `SUPPORT_TICKETS`.

## Roadmap talking points for Lesson 1

- "Once we have destinations, we build an actual audience — a segment — and sync it. We'll do
  this three times, each teaching something different: a simple filter, a filter across two
  tables, and how to exclude people from a send without building a whole new segment."
- Reference the use-cases table in `../use-cases.md` if the colleague wants the full mapping now.

## To build before this becomes a full lesson

- Depends on Module 3 (destinations) being built out first.
- Decide the exact Customer Studio vs. SQL-model path for each use case's segment definition —
  Lesson 2 already taught both, so this is about choosing which is more natural for each filter.
