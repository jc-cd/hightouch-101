# Relationships — TollWay

## Entity relationship diagram

```mermaid
erDiagram
    CUSTOMERS ||--o{ VEHICLES : "owns"
    CUSTOMERS ||--o{ TRIPS : "takes"
    CUSTOMERS ||--o{ TOPUPS : "recharges"
    CUSTOMERS ||--o{ SUPPORT_TICKETS : "raises"
    VEHICLES ||--o{ TRIPS : "used on"
    GANTRIES ||--o{ TRIPS : "charges"

    CUSTOMERS {
        varchar customer_id PK
        varchar account_type
        varchar customer_segment
        varchar loyalty_tier
        varchar topup_mode
        numeric account_balance
        varchar marketing_email_subscribe
    }
    VEHICLES {
        varchar vehicle_id PK
        varchar customer_id FK
        varchar vehicle_type
        varchar tag_type
    }
    GANTRIES {
        varchar gantry_id PK
        varchar road_name
        varchar state
        numeric base_rate_per_km
    }
    TRIPS {
        varchar trip_id PK
        varchar customer_id FK
        varchar vehicle_id FK
        varchar gantry_id FK
        timestamp trip_datetime
        numeric toll_amount
    }
    TOPUPS {
        varchar topup_id PK
        varchar customer_id FK
        timestamp topup_datetime
        numeric amount
        varchar status
    }
    SUPPORT_TICKETS {
        varchar ticket_id PK
        varchar customer_id FK
        varchar status
        varchar category
    }
```

`CUSTOMERS` is the identity spine. Every other table hangs off `customer_id`. `TRIPS` is the
only table with two FKs beyond `customer_id` (`vehicle_id`, `gantry_id`) — it's the busiest join
in the dataset and the one Module 2's single customer view has to handle.

## Architecture — sources to destinations (current, v1)

```mermaid
flowchart TB
    subgraph row1[" "]
        direction LR
        SF["Snowflake — DEMO_DB.HT101_TW<br/>CUSTOMERS · VEHICLES · GANTRIES<br/>TRIPS · TOPUPS · SUPPORT_TICKETS"] -->|source connection| HT[Hightouch]
        HT -->|SQL model / Customer Studio| SCV[Single Customer View]
    end
    subgraph row2[" "]
        direction LR
        BR[Braze] -->|Canvas send| Email[Mock email / Canvas]
        SF2[Snowflake — write-back tables]
    end
    SCV -->|segment + sync| BR
    SCV -->|reverse-ETL sync| SF2

    style SF fill:#1A1A2E,stroke:#2a2a44,color:#fff
    style HT fill:#1A1A2E,stroke:#2a2a44,color:#fff
    style BR fill:#1A1A2E,stroke:#2a2a44,color:#fff
    style row1 fill:transparent,stroke:transparent
    style row2 fill:transparent,stroke:transparent
```

(Split into two shorter rows of ~3 nodes each — the six tables are also listed inside a single
Snowflake box rather than as six separate nodes — same information, far less horizontal width
either way, which matters for legibility once this renders large. A single 6-node horizontal row
was still too wide to stay legible even after that first consolidation.)

Module 1 builds the Snowflake→Hightouch connection and the first raw SQL model. Module 2 builds
the single customer view. Module 3 adds the Braze and Snowflake reverse-ETL destinations.
Module 4 builds the segment/sync/send. BigQuery is not part of this diagram for v1 — see
`inconsistencies.md`.

## Closing the loop (Module 5 — the payload the whole course builds toward)

```mermaid
flowchart TB
    subgraph row1[" "]
        direction LR
        UC1[UC1: Loyalty upsell segment] -->|sync| Send[Braze Canvas send]
        Send -->|opens / clicks| Currents[Braze Currents / Data Share]
    end
    subgraph row2[" "]
        direction LR
        Eng[Snowflake: engagement table] -->|re-queried| HT2[Hightouch: refined model]
        HT2 -->|branches audience| Refined[Refined re-engagement segment]
        Refined -->|sync| Send2[Braze: next-best-action send]
    end
    Currents -->|writes engagement events| Eng

    style UC1 fill:#1A1A2E,stroke:#2a2a44,color:#fff
    style HT2 fill:#1A1A2E,stroke:#2a2a44,color:#fff
    style Eng fill:#1A1A2E,stroke:#2a2a44,color:#fff
    style row1 fill:transparent,stroke:transparent
    style row2 fill:transparent,stroke:transparent
```

(Split into two shorter rows of 3 nodes each, connected top-to-bottom, instead of one long
6-node horizontal chain — the single-row version was too wide to stay legible once rendered
large.)

This is the single diagram that ties Modules 1–5 together: the loyalty segment built in Module 4
(UC1) sends a campaign, Braze's own engagement data flows back into the same Snowflake schema
the colleague built in Module 1, and Hightouch re-queries it to build a segment that's smarter
than anything available on day one. This table doesn't exist yet — it gets built when Module 5's
lesson content is written.
