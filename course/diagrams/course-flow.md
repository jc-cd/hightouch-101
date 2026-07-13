# Course Flow (generic)

```mermaid
flowchart TD
    M1["Module 1<br/>Stand up the CDP"] --> M2["Module 2<br/>Single customer view"]
    M2 --> M3["Module 3<br/>Destinations"]
    M3 --> M4["Module 4<br/>Segments + activation"]
    M4 --> M5["Module 5<br/>Closing the loop"]
    M5 -.feeds back into.-> M4

    classDef deep fill:#1A1A2E,stroke:#00D4FF,color:#fff
    classDef roadmap fill:#1A1A2E,stroke:#2a2a44,color:#cfd0e0

    class M1,M2 deep
    class M3,M4,M5 roadmap
```

Cyan-bordered modules are today's deep dive; grey-bordered modules are roadmap-only for now.
This coloring is a template — update per lesson as later modules move from roadmap to deep dive.
