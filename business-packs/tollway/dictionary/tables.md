# Table Dictionary — DEMO_DB.HT101_TW

All six tables live in one dedicated Snowflake schema. No BigQuery in v1 — see `inconsistencies.md`.

## CUSTOMERS (1,000 rows)

The account holder. One row per TollWay toll account (an "account" can be an individual or a
small business — see `customer_segment`).

| Column | Type | Notes |
|---|---|---|
| `customer_id` | VARCHAR PK | `ht101_tw_cust_000001` … `ht101_tw_cust_001000` |
| `account_type` | VARCHAR | `etag` (55%) / `video_tolling` (35%) / `visitor_pass` (10%) |
| `customer_segment` | VARCHAR | `individual` (88%) / `small_business` (12%) |
| `business_name` | VARCHAR | populated only when `customer_segment = 'small_business'`, else empty |
| `first_name`, `last_name` | VARCHAR | contact person on the account |
| `email` | VARCHAR | `@example.com`, index-suffixed, never deliverable |
| `phone` | VARCHAR | AU mobile format |
| `dob` | DATE | triangular skew, 18–80, mode ~40 |
| `home_state` | VARCHAR | `NSW` (45%) / `VIC` (30%) / `QLD` (15%) / other AU state (10%) |
| `home_city`, `postal` | VARCHAR | state-matched |
| `time_zone` | VARCHAR | matches `home_state` |
| `signup_date` | DATE | triangular skew over a synthetic 3-year window |
| `account_status` | VARCHAR | `active` (92%) / `suspended` (5%) / `closed` (3%) |
| `loyalty_tier` | VARCHAR | `bronze` (55%) / `silver` (32%) / `gold` (13%) — drives trip-volume weighting in `TRIPS`, not independent |
| `payment_method_linked` | BOOLEAN | ~85% true |
| `topup_mode` | VARCHAR | `auto` (55%) / `manual` (35%) / `none` (10%) |
| `auto_topup_threshold` | NUMBER(6,2), nullable | only set when `topup_mode = 'auto'` — one of $10/$20/$30 |
| `account_balance` | NUMBER(10,2) | independently randomized, **not** derived from `TOPUPS`/`TRIPS` — see `inconsistencies.md` |
| `marketing_email_subscribe` | VARCHAR | `subscribed` (90%) / `unsubscribed` (8%) / `opted_in` (2%) — Braze `email_subscribe` semantics |
| `sms_subscribe` | BOOLEAN | secondary channel flag, ~45% true |

No pre-computed aggregates (trip count, lifetime spend, top-up total) live on this table by
design — deriving those is the point of Module 2's single customer view exercise.

## VEHICLES (1,407 rows with default seed; varies by seed)

| Column | Type | Notes |
|---|---|---|
| `vehicle_id` | VARCHAR PK | `ht101_tw_veh_<customer suffix>_<seq>` |
| `customer_id` | VARCHAR FK → `CUSTOMERS` | |
| `rego_plate` | VARCHAR | AU-style, digit count varies slightly by state |
| `state_registered` | VARCHAR | matches customer's `home_state` |
| `vehicle_type` | VARCHAR | `car` (70%) / `suv` (20%) / `motorcycle` (5%) / `light_truck` (4%) / `heavy_truck` (1%) |
| `tag_type` | VARCHAR | correlated to the customer's `account_type`: `etag` → `etag_transponder`, `video_tolling` → `video_matched`, `visitor_pass` → `none` |
| `date_added` | DATE | |
| `is_active` | BOOLEAN | ~95% true |

`individual` customers get 1 vehicle (rarely 2, 8% chance). `small_business` customers get a
fleet of 2–8. This is the second table a colleague has to join in Module 2 — teaches multi-table
SCV construction without needing a second warehouse.

## GANTRIES (48 rows, hand-authored, not generated)

Fixed reference data — TollWay's fictional road network. No script generates this; it's
authored directly in `mock-data/seed-data/gantries.csv` and never changes between re-generations.

| Column | Type | Notes |
|---|---|---|
| `gantry_id` | VARCHAR PK | `ht101_tw_gan_0001` … `ht101_tw_gan_0048` |
| `road_name` | VARCHAR | fictional (e.g. Skyline Freeway, Harbourlink Tunnel) — see `inconsistencies.md` |
| `locality` | VARCHAR | suburb |
| `state` | VARCHAR | `NSW` / `VIC` / `QLD` only |
| `gantry_type` | VARCHAR | `mainline` / `ramp` |
| `base_rate_per_km` | NUMBER(6,2) | used by `generate_trips.py` to derive `TRIPS.toll_amount` |

## TRIPS (10,000 rows, fixed exact total)

One row per toll-gantry charge event — matches how real toll operators actually bill (per
gantry passed, not per point-A-to-B journey).

| Column | Type | Notes |
|---|---|---|
| `trip_id` | VARCHAR PK | `ht101_tw_trip_0000001` … `_0010000` |
| `customer_id` | VARCHAR FK → `CUSTOMERS` | |
| `vehicle_id` | VARCHAR FK → `VEHICLES` | always one of that customer's own vehicles |
| `gantry_id` | VARCHAR FK → `GANTRIES` | 75% chance it's in the customer's home state, 25% chance any state (interstate travel) |
| `trip_datetime` | TIMESTAMP_NTZ | last 12 months, AM/PM peak-hour humps (7–9am / 4–6pm, 40/40/20 split vs. off-peak) |
| `distance_km` | NUMBER(6,2) | 2–15 km per gantry segment |
| `vehicle_class` | VARCHAR | `light` / `heavy` — derived from the chosen vehicle's `vehicle_type`, not independently random |
| `toll_amount` | NUMBER(8,2) | `distance_km × GANTRIES.base_rate_per_km × class_multiplier` (heavy = 2.5×, light = 1×) |
| `payment_status` | VARCHAR | `charged` (92%) / `pending` (5%) / `failed` (3%) |

**Volume distribution**: ~12% of customers get exactly zero trips. The rest draw a weight from a
loyalty-tier-scaled Gamma distribution (gold accounts skew toward far more trips than bronze),
then all 10,000 rows are assigned via a weighted lottery — guarantees the total is exactly
10,000 while producing a realistic long-tail skew. See `generate_trips.py` docstring for the
exact parameters.

## TOPUPS (5,879 rows with default seed; varies by seed)

Payment/recharge transaction history. Not introduced until Module 4 (low-balance use case).

| Column | Type | Notes |
|---|---|---|
| `topup_id` | VARCHAR PK | `ht101_tw_topup_0000001` … |
| `customer_id` | VARCHAR FK → `CUSTOMERS` | |
| `topup_datetime` | TIMESTAMP_NTZ | last 12 months |
| `amount` | NUMBER(8,2) | common tiers $20/$40/$60/$100 (85%), custom amount otherwise |
| `topup_method` | VARCHAR | `auto_recharge` / `manual_card` / `manual_bank` / `cash_retail` |
| `status` | VARCHAR | `success` (95% baseline) / `failed` (5% baseline) |

**Seeded cohort**: ~8% of customers (`--low-balance-pct`, default 0.08) get a manufactured
pattern — a couple of older successful top-ups, then only failed attempts in the trailing 30
days, no success since. Guarantees Module 4's low-balance segment has a stable population. See
`inconsistencies.md`.

## SUPPORT_TICKETS (374 rows with default seed; varies by seed)

Not introduced until Module 4 (suppression use case).

| Column | Type | Notes |
|---|---|---|
| `ticket_id` | VARCHAR PK | `ht101_tw_ticket_000001` … |
| `customer_id` | VARCHAR FK → `CUSTOMERS` | |
| `opened_datetime` | TIMESTAMP_NTZ | |
| `closed_datetime` | TIMESTAMP_NTZ, nullable | only set when `status = 'closed'` |
| `status` | VARCHAR | `closed` (80% baseline) / `open` (15% baseline) / `escalated` (5% baseline) |
| `category` | VARCHAR | `billing_dispute` / `tag_fault` / `account_access` / `general_enquiry` / `toll_notice_dispute` |
| `channel` | VARCHAR | `phone` / `email` / `app` / `web_form` |
| `priority` | VARCHAR | `low` / `medium` / `high` |

**Seeded cohort**: ~6% of customers (`--open-ticket-pct`, default 0.06) are guaranteed a
currently-open ticket opened in the last 14 days. Guarantees Module 4's suppression segment has
a stable population.

## Module 5 addition (not yet built)

Module 5 ("closing the loop") will add an engagement table — Braze Canvas send/open/click
events synced back via Currents/Data Share — that doesn't exist yet as of this dictionary
version. It'll be documented here once Module 5's lesson content is built out.
