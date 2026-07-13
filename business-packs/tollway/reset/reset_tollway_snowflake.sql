/*
  reset_tollway_snowflake.sql

  Wipes DEMO_DB.HT101_TW completely — including any ad-hoc tables/views a
  colleague created while practicing the Module 2 SQL-model path — and
  recreates an empty schema. Safe because HT101_TW is TollWay's own
  dedicated schema; nothing else in DEMO_DB is touched.

  After running this, reload data:
    1. Regenerate the 6 CSVs (see ../mock-data/) or reuse existing ones in ../mock-data/out/
    2. Re-run ../mock-data/load/load_snowflake.sql
*/

DROP SCHEMA IF EXISTS DEMO_DB.HT101_TW CASCADE;
CREATE SCHEMA DEMO_DB.HT101_TW;
