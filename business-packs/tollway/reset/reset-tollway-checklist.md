# TollWay Reset Checklist (instantiated)

Follows `../../course/reset/hightouch-braze-checklist-template.md`'s ordering. Object names
below use the naming convention this pack's lessons establish — update this list with the
colleague's actual object names as they get built (names may vary slightly from what's listed
here if the colleague names things differently mid-lesson).

## Snowflake

Run `reset_tollway_snowflake.sql`, then reload from `../mock-data/load/load_snowflake.sql`.

## Hightouch

1. **Syncs**: any sync named `TollWay - *` (e.g. `TollWay - Loyalty Upsell to Braze`, `TollWay - Low Balance Nudge to Braze`).
2. **Segments**: `TollWay - Loyalty Upsell (UC1)`, `TollWay - Low Balance Nudge (UC2)`, any Customer Studio audience built for UC3's exclusion.
3. **SQL Models**: `TollWay - Customers (raw)`, `TollWay - Trips (raw)`, `TollWay - Vehicles (raw)`, `TollWay - Single Customer View (SQL)`, and any Module 4/5 models.
4. **Customer Studio identity resolution config**: the TollWay identity graph (Customers as primary, Vehicles + Trips as related sources).
5. **Destinations**: the TollWay Braze destination, the TollWay Snowflake reverse-ETL destination.
6. **Sources**: the `DEMO_DB.HT101_TW` Snowflake source connection.

## Braze

1. **Canvases**: any Canvas named `HT101 TW — *`.
2. **Campaigns**: same naming pattern.
3. **Segments**: TollWay segments synced from Hightouch — verify no Canvas/Campaign still references them first.
4. **Tags / content blocks / catalogs** created for TollWay exercises.
5. **Currents / Data Share**: disable the TollWay export config before removing its Snowflake write-back destination.
6. **Test profiles**: dashboard search `external_id starts with ht101_tw_` → select all → delete. At ~1,000 profiles this is a single page or two, no need for bulk-purge tooling.
7. **Custom attributes / subscription groups** created for TollWay, if not reused by a later business pack.

## After reset

Confirm the row-count query in `../dictionary/cheatsheet.md` returns zero for all 6 tables
before reloading, so the next colleague genuinely starts from zero.
