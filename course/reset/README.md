# Reset — Index

Two different reset mechanisms, for two different reasons:

| Platform | Mechanism | Why |
|---|---|---|
| Snowflake (warehouse) | **Scripted** — drop and recreate the pack's dedicated schema | Schema-level isolation makes this safe and total: nothing outside the pack's schema is touched, and it catches ad-hoc objects a colleague creates while practicing (a `TRUNCATE`-per-known-table script wouldn't). |
| Hightouch + Braze | **Manual checklist** — documented, dependency-ordered, step-by-step | Colleagues are new to these platforms and the sandbox is shared with other learners' and other packs' objects — a script they don't yet understand is a bigger risk in a shared account than a slower manual walkthrough. Object deletion order matters (a Canvas must go before the segment it targets) and a human doing it step by step catches "wait, this is blocked, why?" moments that are themselves a useful platform-mechanics lesson. |

`warehouse-reset-template.md` and `hightouch-braze-checklist-template.md` are generic — real
object names get filled in per business pack (see `../../business-packs/tollway/reset/`).
