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

## Presenting live — the generated site

`../../tools/build_site.py` generates a browsable multi-page site from this dictionary plus every
other `.md` doc in the course/pack, output to `../../docs/` (published at
https://jc-cd.github.io/hightouch-101/). This dictionary's diagrams render on the site's
"Relationships & Diagrams" page straight from `relationships.md`'s Mermaid source — no manual
mirroring into a separate HTML file anymore. Rerun the generator after editing any doc:
`python3 ../../tools/build_site.py`.

## Source of truth hierarchy

1. The actual generator scripts in `../mock-data/` are canonical for exact distributions and ID formats.
2. `../CLAUDE.md` (pack-level) and `../../CLAUDE.md` (course-level) are canonical for naming/reset conventions.
3. This dictionary distils both into a single reference. If anything here disagrees with the generator code, the code wins.

## Not in scope

- Auto-generation from `INFORMATION_SCHEMA` — hand-curated from the generator specs.
- Anything about Hightouch models/segments/syncs or Braze Canvases/campaigns once those get built — that's lesson content, not dictionary content, since it changes as the colleague builds and rebuilds it.
