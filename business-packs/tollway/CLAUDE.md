# TollWay Business Pack

## What this is

Business-pack #1 for the Hightouch 101 course (`../../CLAUDE.md`). A fictional AU toll-road
operator — see `brief.md` for the business model, `use-cases.md` for the four segmentation
exercises, `dictionary/` for the data.

## Stack / sandbox targets

- **Snowflake**: `DEMO_DB.HT101_TW` schema — `CUSTOMERS`, `VEHICLES`, `GANTRIES`, `TRIPS`,
  `TOPUPS`, `SUPPORT_TICKETS`. No BigQuery in v1 (see `dictionary/inconsistencies.md` #7).
- **Hightouch**: sandbox workspace, objects prefixed/tagged `ht101_tw` where the UI allows tagging.
- **Braze**: sandbox workspace, `external_id` prefix `ht101_tw_`, campaign/Canvas names prefixed `HT101 TW —`.

## Conventions specific to this pack

- Never create a warehouse object outside `DEMO_DB.HT101_TW` — that schema-level isolation is
  what makes the Snowflake reset (`reset/reset_tollway_snowflake.sql`) safe to run without
  touching any other schema in the shared `DEMO_DB` database (which has other tenants — see the
  `DEMO_DATA` schema's pre-existing `CUSTOMERS_TOLLS` table, untouched by this project).
- Table names inside `HT101_TW` are plain (`CUSTOMERS`, not `HT101_TW_CUSTOMERS`) — the schema
  already scopes them.
- Mock data generators live in `mock-data/`, output CSVs land in `mock-data/out/` (gitignored —
  regenerate, don't hand-edit).
- Lesson docs (`lessons/`) contain 📸 screenshot-checkpoint markers where the colleague should
  capture their own live Hightouch/Braze/Snowflake UI state — nobody else can pre-supply those
  screenshots since they depend on the sandbox account's live state.
- All SQL in this pack (lessons, cheatsheet, load script) fully qualifies every table reference
  as `DEMO_DB.HT101_TW.<table>`, never a bare table name — `DEMO_DB` has other schemas
  (`DEMO_DATA`, plus whatever Hightouch itself provisions) with objects that collide on name
  (a bare `CUSTOMERS` load once resolved into `DEMO_DATA` by accident; a bare `SUPPORT_TICKETS`
  load once silently defaulted to no-header-row parsing). Always qualify.

## Presenting this pack

There's no more standalone `overview.html`/`diagrams.html` — superseded by the multi-page site
generated from `../../tools/build_site.py` (reads every `.md` in this pack and `course/`, never
modifies them, outputs to `../../docs/`). Rerun the generator after editing any source doc;
`../../docs/` is committed output, not something colleagues edit directly.

## Status

- Mock data generators + Snowflake load: **done and live**. All six tables loaded into
  `DEMO_DB.HT101_TW` via the Snowsight "Load Data into a Table" wizard and verified 2026-07-13 —
  `CUSTOMERS` 1,000 / `VEHICLES` 1,407 / `GANTRIES` 48 / `TRIPS` 10,000 / `TOPUPS` 5,879 /
  `SUPPORT_TICKETS` 374. `mock-data/load/load_snowflake.sql` is kept as the canonical reference
  schema and fallback path, not what actually ran.
- All 5 modules' lessons are now full depth. Lesson 1 (2026-07-14) still only *previews*
  Modules 3–5 at roadmap level — running them for real is later-session material. Module 5
  additionally needs a Braze Data Share provisioned ahead of time; see that lesson's opening note.
- Not yet done: connecting the Hightouch sandbox to `DEMO_DB.HT101_TW` as a source (Lesson 1,
  step 2) — first live test of that connection is either a pre-lesson dry run or happens live
  with the colleague tomorrow.
