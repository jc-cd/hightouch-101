# Hightouch 101 — Syllabus

Vertical-agnostic module list. Concrete lesson content for each module lives in the business
pack (e.g. `../business-packs/tollway/lessons/`) — this doc is the pedagogy, not the click path.

## Modules

| # | Module | Objective |
|---|---|---|
| 1 | Stand up the CDP | Connect a warehouse source to Hightouch, understand source vs. model, run a first raw SQL model, verify row counts against the source |
| 2 | Single customer view | Build the same customer-level view two ways — Hightouch Customer Studio identity resolution, and a hand-written SQL model — and compare governance/speed vs. control/transparency |
| 3 | Destinations | Configure a reverse-ETL destination (Braze) and a warehouse write-back destination (Snowflake) |
| 4 | Segments + activation | Build a segment, sync it to a destination, trigger a real send (campaign or Canvas) |
| 5 | Closing the loop | Get engagement data back from the activation platform into the warehouse, re-query it in Hightouch, build a segment that's smarter than what was possible on day one |

"Simulate a real business as much as possible" isn't a module — it's a cross-cutting design
principle applied to every business pack's data, use cases, and lesson framing, not a syllabus
line item.

## Lesson 1 pacing (2026-07-14)

| Module | Treatment | Est. duration |
|---|---|---|
| 1 | **Deep dive** | 60–75 min |
| 2 | **Deep dive** | 75–90 min |
| 3 | Roadmap overview | 15 min |
| 4 | Roadmap overview | 15 min |
| 5 | Roadmap overview | 15 min |

Total ≈ 3–3.5 hours including Q&A — long for one sitting. **Recommendation**: split into two
half-sessions if the calendar allows (Session 1a: Module 1 + roadmap intro; Session 1b: Module 2
+ roadmap continuation) rather than compress the deep-dive content. Make the live call based on
how Module 1 is landing — if the colleague is moving fast, keep going; if concepts are taking
longer to land, better to bank a strong Module 1 and pick up Module 2 fresh next time than rush
through both in one sitting.

## Later sessions

Modules 3–5 now have full lesson-doc treatment (concrete click paths, screenshot checkpoints) in
the business pack's `lessons/` folder — Lesson 1 only *previews* them at roadmap level; running
them for real is later-session material, each substantial enough to warrant its own sitting:
Module 3 (~45–60 min), Module 4 (~120–150 min — the longest lesson, real Braze segment/Canvas
builds for all three use cases, worth splitting across two sittings), Module 5 (~60–75 min, plus
lead time to get a Braze Data Share provisioned before it can run at all — see the lesson doc's
"Before this lesson" note).
