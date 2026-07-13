# Known Deviations and Limitations — TollWay

Documentation only. These are deliberate design choices for a training dataset, not bugs — but
worth knowing so nobody "fixes" them or gets confused mid-lesson.

| # | Deviation | Why |
|---|---|---|
| 1 | AU-only geography, no NZ split | The house mock-data convention (`generate_customers.py` in `amperity-braze-lambda-connector-internal`) uses a 90/10 AU/NZ split. TollWay drops NZ entirely — toll roads are an AU capital-city phenomenon (NSW/VIC/QLD), and there's no NZ equivalent to model realistically. |
| 2 | Fictional road/toll names | `GANTRIES.road_name` uses invented names (Skyline Freeway, Harbourlink Tunnel, etc.), not real Australian toll road names — TollWay itself is a fictional operator, not a real one, per the training-material naming decision. |
| 3 | `CUSTOMERS.account_balance` is independent of `TOPUPS`/`TRIPS` | A real balance would be `opening_balance + SUM(topups.amount) - SUM(trips.toll_amount)`. Here it's randomized independently for generator simplicity. Don't build a lesson exercise that expects the balance to reconcile against transaction history — it won't. |
| 4 | UC2 and UC3 populations are seeded, not organic | `generate_topups.py` (`--low-balance-pct`, default 8%) and `generate_support_tickets.py` (`--open-ticket-pct`, default 6%) deliberately manufacture a guaranteed-matching cohort for each use case, rather than relying on chance. Without this, re-running the generators with a different `--seed` could produce a segment with zero or a handful of matches, which would make the lesson unreliable. This is called out explicitly so nobody mistakes the seeded cohort for a real signal worth investigating further. |
| 5 | `TRIPS` models one row per gantry, not per journey | Real driving journeys often cross multiple gantries. This dataset doesn't model journeys as a higher-level entity — each `TRIPS` row is one charge event. Simpler for a first lesson; a "journey" grouping (by customer + vehicle + time-proximity) could be a good later-session SQL exercise, not a v1 requirement. |
| 6 | `GANTRIES` is hand-authored, not generated | Only 48 rows of small fixed reference data — a generator script would add randomization complexity with no training value. Re-running the other generators never changes `GANTRIES`. |
| 7 | No BigQuery in v1 | The original design considered BigQuery for "other" datasets (vehicles, top-ups, support tickets) to teach cross-warehouse source connections. Dropped for v1 — Johan wanted everything in Snowflake to keep the first lesson focused. BigQuery re-enters when a future business-pack vertical genuinely needs a second warehouse to teach that concept properly. |
| 8 | No engagement table yet | Module 5's "closing the loop" engagement table (Braze Currents/Data Share write-back) doesn't exist as of this dictionary version — it's roadmap-only until Module 5's lesson content is built out in a later session. |
