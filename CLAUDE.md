# Hightouch 101 — Internal Training Program

## What This Is

Hands-on training for CD colleagues to learn Hightouch end-to-end: stand up a CDP, build a
single customer view, wire up destinations, activate segments to Braze, and close the loop
with engagement data flowing back into the warehouse. Uses shared CD sandbox accounts
(Hightouch, Snowflake, Braze). BigQuery is out of scope for v1 — everything lives in Snowflake.

## Structure

```
course/            vertical-agnostic shell — pedagogy, platform-mechanics recipes, reset templates
business-packs/    one folder per fictional mock business, each a full self-contained scenario
  tollway/         v1 — fictional AU toll-road operator (see business-packs/tollway/CLAUDE.md)
tools/             build_site.py — generates the presentation site from the .md docs above
site/              generated output (committed) — the actual browsable multi-page site
```

`.md` files under `course/` and `business-packs/` are the canonical source — `tools/build_site.py`
only reads them, never writes back. `site/` is generated output, not hand-edited. Rerun the
generator after any doc change: `python3 tools/build_site.py`.

`course/` doesn't change per business. Only `business-packs/<name>/` changes. A future vertical
(retail, insurance, streaming) gets its own `business-packs/<name>/` mirroring `tollway/`'s file
names, not a rewrite of `course/`.

## Why the split

The concrete stuff (brief, mock data, click-by-click lessons with real object names, instantiated
reset checklists) lives in the business pack, because it's inherently tied to one scenario. The
generic stuff (module objectives/sequencing, how a Hightouch pk_hash model works, how Braze
Currents works, teardown dependency ordering) lives in the shell, because it's true regardless of
which fictional business is running through it.

## Sandbox conventions (apply to every business pack)

- Warehouse: Snowflake only for v1. Each pack gets its own dedicated schema, never `PUBLIC` or a
  shared schema — this is what makes a full reset both total and safe in a shared database.
  TollWay uses `DEMO_DB.HT101_TW`.
- Table names are plain within the pack's own schema (`CUSTOMERS`, `TRIPS`, ...) — the schema
  name already scopes them, so a repeated prefix on every table adds noise for no benefit.
- Braze/Hightouch objects (segments, models, syncs, Canvases, campaigns) and Braze `external_id`
  values use a `<course>_<pack>_` prefix (TollWay: `ht101_tw_`) so they're greppable and safely
  purgeable without touching another pack's or colleague's objects in the same shared sandbox.
- Reset for Hightouch/Braze is a **manual checklist**, not an automated API purge — colleagues are
  new to these platforms and the sandbox is shared, so a documented, dependency-ordered walkthrough
  is safer than a script they don't yet understand. Reset for Snowflake is a script, since dropping
  a dedicated schema is safe and fast.
- Mock data generators are pure-stdlib Python (no pandas/faker), `argparse` with `--count/--out/--seed`
  (deterministic default seeds), stream output via `csv.DictWriter`, use `@example.com` emails
  (RFC 2606 reserved domain — nothing can ever be delivered). Matches the house style in
  `internal/amperity-braze-lambda-connector-internal/mock-data/`.

## Status

- TollWay pack: mock data + course docs in progress, first lesson (Modules 1-2 deep dive) scheduled
  2026-07-14.
