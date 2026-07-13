# Hightouch + Braze Reset Checklist Template (generic)

Manual, not automated — see `README.md` for why. Delete in this order; each step exists because
the platform won't let you delete something still referenced by a later-listed object type.

## Hightouch

1. **Syncs** — delete every sync created for this pack. A sync references a model and a
   destination, so it must go first.
2. **Segments** (Customer Studio audiences) — delete next. If Hightouch blocks a deletion here,
   step 1 was incomplete; go back and find the sync still referencing it.
3. **SQL Models** — delete once no segment or sync still references them.
4. **Customer Studio identity resolution config** — tear down last of the model-layer objects,
   since segments/models above may depend on it existing.
5. **Destinations** — remove once step 1's syncs referencing them are gone.
6. **Sources** — remove last; models depend on the source connection existing.

## Braze

1. **Canvases** — archive or delete first. A Canvas references a segment, and (if configured) a
   Currents/Data Share export — it must go before either.
2. **Campaigns** — same mechanic as Canvases, delete/archive next.
3. **Segments** — only after confirming zero active Canvases/Campaigns still reference them.
   Verify before deleting, don't just attempt it and hope the platform blocks unsafe deletions.
4. **Tags / content blocks / catalogs** created for this pack.
5. **Currents / Data Share export config** — disable before removing the Snowflake destination
   table it writes to, to avoid an orphaned/failing export.
6. **Test user profiles** — bulk-delete via dashboard search filtering on this pack's
   `external_id` prefix.
7. **Custom attributes / subscription groups** created for this pack, if not being reused.

Fill in real object names in the pack's instantiated version once those objects actually exist
(see `../../business-packs/tollway/reset/reset-tollway-checklist.md`).
