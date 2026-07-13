# TollWay Data Dictionary

Reference layer for the synthetic TollWay dataset used across all Hightouch 101 lessons.
This folder is a **reference**, not a lesson — it captures what the data *is*, not how to
click through Hightouch or Braze (that's in `../lessons/`).

## Files

| File | What's in it |
|---|---|
| `tables.md` | Every table in `DEMO_DB.HT101_TW`: columns, types, value distributions, join keys, gotchas. |
| `relationships.md` | Mermaid ERD, the source→Hightouch→destination architecture diagram, and the closing-the-loop diagram that ties Modules 1–5 together. Source of truth for all diagram content. |
| `cheatsheet.md` | Diagnostic queries reused across lessons — row counts, cohort checks, customer lookups. |
| `inconsistencies.md` | Deliberate deviations from realism/house convention, documented so nobody mistakes them for bugs. |

## Presenting live — overview.html

`../overview.html` is the colleague-facing orientation page for Lesson 1 — open it directly in a
browser (no build step, no server) and put it on the screen at the start of the session. It
covers the business scenario, the 6-table dataset with real row counts, today's agenda, the 4
use cases, and the same four diagrams from `relationships.md` (course flow, architecture, ERD,
closing-the-loop), rendered large. Styled after `internal/pulse-health-console/report.html`'s
card/KPI-grid/badge system, which itself matches `internal/amperity-101/`'s color palette.

If a diagram's Mermaid source changes, update `relationships.md` first and mirror the change
into `overview.html` — the `.md` file is the source of truth, the `.html` file is a presentation
view of it. Same rule for row counts, use-case descriptions, and agenda timing: `tables.md`,
`use-cases.md`, and `course/syllabus.md` are canonical, `overview.html` mirrors them.

## Source of truth hierarchy

1. The actual generator scripts in `../mock-data/` are canonical for exact distributions and ID formats.
2. `../CLAUDE.md` (pack-level) and `../../CLAUDE.md` (course-level) are canonical for naming/reset conventions.
3. This dictionary distils both into a single reference. If anything here disagrees with the generator code, the code wins.

## Not in scope

- Auto-generation from `INFORMATION_SCHEMA` — hand-curated from the generator specs.
- Anything about Hightouch models/segments/syncs or Braze Canvases/campaigns once those get built — that's lesson content, not dictionary content, since it changes as the colleague builds and rebuilds it.
