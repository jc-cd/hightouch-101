# Architecture Overview (generic)

```mermaid
flowchart LR
    subgraph Sources
        A[Warehouse source A]
        B[Warehouse source B]
    end

    Sources -->|connect| HT[Hightouch]
    HT -->|SQL model / Customer Studio| SCV[Single Customer View]
    SCV -->|segment + sync| D1[Destination 1 — e.g. Braze]
    SCV -->|reverse-ETL sync| D2[Destination 2 — e.g. warehouse write-back]

    style HT fill:#1A1A2E,stroke:#2a2a44,color:#fff
```

This is the shape every business pack instantiates with real table/object names — see the
pack's `dictionary/relationships.md` for the concrete version (e.g. TollWay's uses one Snowflake
source, no Source B, since BigQuery is out of scope for v1).
