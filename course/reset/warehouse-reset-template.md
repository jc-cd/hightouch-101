# Warehouse Reset Template (generic)

## Pattern

```sql
DROP SCHEMA IF EXISTS <DATABASE>.<PACK_SCHEMA> CASCADE;
CREATE SCHEMA <DATABASE>.<PACK_SCHEMA>;
```

Then re-run that pack's `mock-data/load/load_<warehouse>.sql` to reload data.

## Why drop-and-recreate, not TRUNCATE

A `TRUNCATE TABLE` script has to enumerate every table by name. Anything a colleague creates
while practicing a SQL-model exercise (a scratch table, a test view) isn't on that list and
survives the reset — which defeats "wipe everything and restart from zero." Drop-and-recreate
the whole schema removes everything, known or not, in one step.

## Precondition

This is only safe because the pack has its **own dedicated schema**, never `PUBLIC` or a schema
shared with anything else. If a pack's schema convention is ever violated (someone creates a
table outside it), this reset silently misses that table — which is the actual failure mode to
watch for, not "did the script run."
