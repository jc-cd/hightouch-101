# TollWay — Business Brief

## What TollWay is

TollWay is a **fictional** Australian toll-road operator, built for Hightouch 101 training.
It's modeled on the real business shape of Australian toll operators like Transurban/Linkt —
electronic tolling, distance-based billing, tag and video accounts, loyalty tiers — but every
name, road, and customer in this dataset is invented. No real company data, branding, or
customer records are used anywhere in this course.

## The business model

- Customers hold a **toll account**, one of three types:
  - **e-tag** — a physical transponder in the vehicle; beeps at each gantry, toll deducted automatically.
  - **video tolling** — no tag; a camera matches the rego plate to the account, small extra "vehicle matching" fee.
  - **visitor pass** — prepaid, for occasional or one-off toll road use.
- Billing is **usage-based**, not subscription: every gantry passed on a tolled road generates a charge, calculated from distance travelled and a per-road rate.
- Accounts can be **individual** or **small business** (a business account typically has a small fleet of vehicles under one account).
- Accounts can run **auto top-up** (recharges automatically at a balance threshold) or **manual top-up**, or effectively self-fund via linked payment on account (video tolling/e-tag can run a small negative balance and get billed after the fact — visitor passes are always prepaid).
- TollWay has a **loyalty program** with three tiers — Bronze, Silver, Gold — roughly analogous to real programs like Linkt Rewards. Higher tiers correlate with heavier road usage in this dataset (not with a discount mechanic — that's out of scope for training purposes).

## Why this business shape works well for CDP/Hightouch training

- It has a genuine identity-resolution problem: one customer, multiple vehicles, many trips — a textbook single customer view exercise.
- It has clean, teachable segmentation angles: usage frequency (loyalty upsell), payment risk (low balance), and service friction (support tickets) — three different data shapes, not three copies of the same filter.
- Toll billing is naturally event-heavy (10,000 trip events on 1,000 customers) without being so large it's unwieldy for a first lesson.
- It has an obvious "close the loop" story: send a campaign, watch engagement, use that engagement to build a smarter segment next time — which is exactly what Module 5 teaches.

## Scope note

v1 (this pack) covers only the toll/trips business. Future business-pack verticals (retail,
insurance, streaming) will reuse the same course mechanics (`../../course/`) against a
completely different dataset shape — e.g. a streaming business pack would have subscriptions
and household-ing instead of trips. See `../../CLAUDE.md`.
