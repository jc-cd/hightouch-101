/*
  load_snowflake.sql — TollWay (hightouch-101) mock data load

  Target: DEMO_DB.HT101_TW (dedicated schema, already created).
  Every object below is fully qualified with DEMO_DB.HT101_TW — don't rely on
  a prior USE SCHEMA / USE DATABASE having been run in the same worksheet
  session, since DEMO_DB has other schemas (e.g. DEMO_DATA) that a bare
  table name could resolve into by mistake.

  Status: all six tables are already loaded (as of 2026-07-13) via the
  Snowsight "Load Data into a Table" UI wizard, not this script — that
  wizard auto-detects column names/types per file rather than running
  this DDL. This script is kept as the canonical reference schema and as
  a fallback path (e.g. if the wizard's auto-detect misbehaves on a file,
  as it did for support_tickets.csv, or if this ever needs to run somewhere
  the UI wizard isn't available). Running it now would DROP AND RECREATE
  the tables (CREATE OR REPLACE) — don't run it against the live schema
  without reloading data straight after, or you'll be left with 6 empty
  tables.

  Run this AFTER generating the six CSVs into mock-data/out/:

    python generate_customers.py       --count 1000  --out out/customers.csv
    python generate_vehicles.py        --customers out/customers.csv --out out/vehicles.csv
    python generate_trips.py           --customers out/customers.csv --vehicles out/vehicles.csv \
                                        --gantries seed-data/gantries.csv --count 10000 --out out/trips.csv
    python generate_topups.py          --customers out/customers.csv --out out/topups.csv
    python generate_support_tickets.py --customers out/customers.csv --out out/support_tickets.csv

  gantries.csv is hand-authored — copy seed-data/gantries.csv straight into out/.

  Two ways to get the CSVs into Snowflake:
    (a) Snowsight UI: Data > Add Data > Load data into a table > browse to each CSV.
        Snowsight can create the table for you from the CSV, OR load into a table you
        already created with the DDL below — pick the "select an existing table" path
        so the column types below are the ones that stick. Double-check the "Header"
        option reads "First line contains header" before loading each file — it has
        been seen to default to "no header" for at least one file in this dataset.
    (b) SnowSQL CLI, using the stage + COPY INTO below:
        PUT file://out/customers.csv       @DEMO_DB.HT101_TW.HT101_TW_STAGE AUTO_COMPRESS=TRUE;
        PUT file://out/vehicles.csv        @DEMO_DB.HT101_TW.HT101_TW_STAGE AUTO_COMPRESS=TRUE;
        PUT file://out/trips.csv           @DEMO_DB.HT101_TW.HT101_TW_STAGE AUTO_COMPRESS=TRUE;
        PUT file://out/topups.csv          @DEMO_DB.HT101_TW.HT101_TW_STAGE AUTO_COMPRESS=TRUE;
        PUT file://out/support_tickets.csv @DEMO_DB.HT101_TW.HT101_TW_STAGE AUTO_COMPRESS=TRUE;
        PUT file://seed-data/gantries.csv  @DEMO_DB.HT101_TW.HT101_TW_STAGE AUTO_COMPRESS=TRUE;
      then run the COPY INTO statements below.
*/

CREATE FILE FORMAT IF NOT EXISTS DEMO_DB.HT101_TW.FF_HT101_TW_CSV
  TYPE = CSV
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  EMPTY_FIELD_AS_NULL = TRUE
  NULL_IF = ('');

CREATE STAGE IF NOT EXISTS DEMO_DB.HT101_TW.HT101_TW_STAGE
  FILE_FORMAT = DEMO_DB.HT101_TW.FF_HT101_TW_CSV;

-- === CUSTOMERS ===
CREATE OR REPLACE TABLE DEMO_DB.HT101_TW.CUSTOMERS (
  customer_id                VARCHAR PRIMARY KEY,
  account_type                VARCHAR,
  customer_segment            VARCHAR,
  business_name                VARCHAR,
  first_name                  VARCHAR,
  last_name                    VARCHAR,
  email                        VARCHAR,
  phone                        VARCHAR,
  dob                          DATE,
  home_state                  VARCHAR,
  home_city                    VARCHAR,
  postal                      VARCHAR,
  time_zone                    VARCHAR,
  signup_date                  DATE,
  account_status                VARCHAR,
  loyalty_tier                VARCHAR,
  payment_method_linked        BOOLEAN,
  topup_mode                  VARCHAR,
  auto_topup_threshold        NUMBER(6,2),
  account_balance              NUMBER(10,2),
  marketing_email_subscribe    VARCHAR,
  sms_subscribe                BOOLEAN
);

-- === VEHICLES ===
CREATE OR REPLACE TABLE DEMO_DB.HT101_TW.VEHICLES (
  vehicle_id        VARCHAR PRIMARY KEY,
  customer_id      VARCHAR,
  rego_plate        VARCHAR,
  state_registered  VARCHAR,
  vehicle_type      VARCHAR,
  tag_type          VARCHAR,
  date_added        DATE,
  is_active        BOOLEAN
);

-- === GANTRIES ===
CREATE OR REPLACE TABLE DEMO_DB.HT101_TW.GANTRIES (
  gantry_id          VARCHAR PRIMARY KEY,
  road_name          VARCHAR,
  locality          VARCHAR,
  state              VARCHAR,
  gantry_type        VARCHAR,
  base_rate_per_km  NUMBER(6,2)
);

-- === TRIPS ===
CREATE OR REPLACE TABLE DEMO_DB.HT101_TW.TRIPS (
  trip_id            VARCHAR PRIMARY KEY,
  customer_id        VARCHAR,
  vehicle_id        VARCHAR,
  gantry_id          VARCHAR,
  trip_datetime      TIMESTAMP_NTZ,
  distance_km        NUMBER(6,2),
  vehicle_class      VARCHAR,
  toll_amount        NUMBER(8,2),
  payment_status    VARCHAR
);

-- === TOPUPS ===
CREATE OR REPLACE TABLE DEMO_DB.HT101_TW.TOPUPS (
  topup_id          VARCHAR PRIMARY KEY,
  customer_id      VARCHAR,
  topup_datetime    TIMESTAMP_NTZ,
  amount            NUMBER(8,2),
  topup_method      VARCHAR,
  status            VARCHAR
);

-- === SUPPORT_TICKETS ===
CREATE OR REPLACE TABLE DEMO_DB.HT101_TW.SUPPORT_TICKETS (
  ticket_id          VARCHAR PRIMARY KEY,
  customer_id        VARCHAR,
  opened_datetime    TIMESTAMP_NTZ,
  closed_datetime    TIMESTAMP_NTZ,
  status            VARCHAR,
  category          VARCHAR,
  channel            VARCHAR,
  priority          VARCHAR
);

-- === Load (SnowSQL / stage path — run the PUT commands above first) ===
COPY INTO DEMO_DB.HT101_TW.CUSTOMERS FROM @DEMO_DB.HT101_TW.HT101_TW_STAGE/customers.csv.gz FILE_FORMAT = (FORMAT_NAME = DEMO_DB.HT101_TW.FF_HT101_TW_CSV);
COPY INTO DEMO_DB.HT101_TW.VEHICLES FROM @DEMO_DB.HT101_TW.HT101_TW_STAGE/vehicles.csv.gz FILE_FORMAT = (FORMAT_NAME = DEMO_DB.HT101_TW.FF_HT101_TW_CSV);
COPY INTO DEMO_DB.HT101_TW.GANTRIES FROM @DEMO_DB.HT101_TW.HT101_TW_STAGE/gantries.csv.gz FILE_FORMAT = (FORMAT_NAME = DEMO_DB.HT101_TW.FF_HT101_TW_CSV);
COPY INTO DEMO_DB.HT101_TW.TRIPS FROM @DEMO_DB.HT101_TW.HT101_TW_STAGE/trips.csv.gz FILE_FORMAT = (FORMAT_NAME = DEMO_DB.HT101_TW.FF_HT101_TW_CSV);
COPY INTO DEMO_DB.HT101_TW.TOPUPS FROM @DEMO_DB.HT101_TW.HT101_TW_STAGE/topups.csv.gz FILE_FORMAT = (FORMAT_NAME = DEMO_DB.HT101_TW.FF_HT101_TW_CSV);
COPY INTO DEMO_DB.HT101_TW.SUPPORT_TICKETS FROM @DEMO_DB.HT101_TW.HT101_TW_STAGE/support_tickets.csv.gz FILE_FORMAT = (FORMAT_NAME = DEMO_DB.HT101_TW.FF_HT101_TW_CSV);

-- === Verify row counts (confirmed live 2026-07-13: 1,000 / 1,407 / 48 / 10,000 / 5,879 / 374 — vehicle/topup/ticket counts vary if you regenerate with a different --seed) ===
SELECT 'CUSTOMERS' AS table_name, COUNT(*) AS row_count FROM DEMO_DB.HT101_TW.CUSTOMERS
UNION ALL
SELECT 'VEHICLES', COUNT(*) FROM DEMO_DB.HT101_TW.VEHICLES
UNION ALL
SELECT 'GANTRIES', COUNT(*) FROM DEMO_DB.HT101_TW.GANTRIES
UNION ALL
SELECT 'TRIPS', COUNT(*) FROM DEMO_DB.HT101_TW.TRIPS
UNION ALL
SELECT 'TOPUPS', COUNT(*) FROM DEMO_DB.HT101_TW.TOPUPS
UNION ALL
SELECT 'SUPPORT_TICKETS', COUNT(*) FROM DEMO_DB.HT101_TW.SUPPORT_TICKETS;
