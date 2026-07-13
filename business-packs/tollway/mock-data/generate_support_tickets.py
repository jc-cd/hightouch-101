#!/usr/bin/env python3
"""
generate_support_tickets.py

Generates a CSV of TollWay support tickets. Most customers have zero
tickets (avg-per-customer default 0.3, Poisson-distributed) — realistic
for a low-friction toll account.

A deliberately seeded cohort (--open-ticket-pct, default 6% of
customers) is guaranteed a currently-open ticket, so the "suppress
campaign for customers with an open complaint" use case in Module 4
has a stable, non-trivial population regardless of the random seed.
Documented in dictionary/inconsistencies.md.

Usage:
    python generate_support_tickets.py --customers out/customers.csv --out out/support_tickets.csv
"""

import argparse
import csv
import math
import os
import random
import sys
from datetime import datetime, timedelta

CATEGORIES = ["billing_dispute", "tag_fault", "account_access", "general_enquiry", "toll_notice_dispute"]
CHANNELS = ["phone", "email", "app", "web_form"]

def weighted_choice(rng, pairs):
    r = rng.random()
    upper = 0.0
    for value, w in pairs:
        upper += w
        if r < upper:
            return value
    return pairs[-1][0]

def poisson(rng, lam):
    l_bound = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= l_bound:
            return k - 1

def build_ticket(customer_id, rng, now, forced_status=None):
    priority = weighted_choice(rng, [("low", 0.5), ("medium", 0.35), ("high", 1.0)])
    category = rng.choice(CATEGORIES)
    channel = rng.choice(CHANNELS)

    if forced_status == "open":
        opened_days_ago = rng.randint(0, 13)
        status = "open"
    else:
        opened_days_ago = rng.randint(0, 364)
        status = weighted_choice(rng, [("closed", 0.80), ("open", 0.95), ("escalated", 1.0)])

    opened_dt = now - timedelta(days=opened_days_ago)
    closed_dt = ""
    if status == "closed":
        resolve_days = rng.randint(0, 7)
        closed_dt = (opened_dt + timedelta(days=resolve_days)).isoformat(sep=" ")

    return {
        "customer_id": customer_id,
        "opened_datetime": opened_dt.isoformat(sep=" "),
        "closed_datetime": closed_dt,
        "status": status,
        "category": category,
        "channel": channel,
        "priority": priority,
    }

HEADER = ["ticket_id", "customer_id", "opened_datetime", "closed_datetime", "status", "category", "channel", "priority"]

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--customers", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--avg-per-customer", type=float, default=0.3)
    p.add_argument("--open-ticket-pct", type=float, default=0.06)
    p.add_argument("--seed", type=int, default=4)
    args = p.parse_args()

    rng = random.Random(args.seed)
    now = datetime(2026, 7, 13, 12, 0, 0)

    with open(args.customers, encoding="utf-8", newline="") as f:
        customers = list(csv.DictReader(f))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    total, seeded = 0, 0
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        ticket_seq = 0
        for c in customers:
            rows = []
            if rng.random() < args.open_ticket_pct:
                seeded += 1
                rows.append(build_ticket(c["customer_id"], rng, now, forced_status="open"))
            count = poisson(rng, args.avg_per_customer)
            for _ in range(count):
                rows.append(build_ticket(c["customer_id"], rng, now))
            for row in rows:
                ticket_seq += 1
                row["ticket_id"] = f"ht101_tw_ticket_{ticket_seq:06d}"
                writer.writerow(row)
            total += len(rows)

    print(f"Done — {total:,} tickets across {len(customers):,} customers", file=sys.stderr)
    print(f"  seeded open-ticket customers: {seeded:,} ({seeded/len(customers):.1%})", file=sys.stderr)
    print(f"Output: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
