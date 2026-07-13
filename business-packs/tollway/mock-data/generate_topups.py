#!/usr/bin/env python3
"""
generate_topups.py

Generates a CSV of TollWay account top-up (recharge) transactions.
Reads customers.csv and generates a Poisson-distributed count of
top-ups per customer over the trailing 12 months.

A deliberately seeded cohort (--low-balance-pct, default 8% of
customers) gets a manufactured pattern: a couple of older successful
top-ups, then only failed top-ups in the trailing 30 days and no
success since — so the "low balance / auto top-up off" segment used
in Module 4 has a stable, non-trivial population regardless of the
random seed, rather than depending on chance. This is a documented,
deliberate deviation from pure randomness — see dictionary/inconsistencies.md.

Usage:
    python generate_topups.py --customers out/customers.csv --out out/topups.csv
    python generate_topups.py --customers out/customers.csv --out out/topups.csv \
        --avg-per-customer 6 --low-balance-pct 0.08 --seed 3
"""

import argparse
import csv
import math
import os
import random
import sys
from datetime import datetime, timedelta

AMOUNT_TIERS = [20, 40, 60, 100]
METHODS = ["auto_recharge", "manual_card", "manual_bank", "cash_retail"]

def weighted_choice(rng, pairs):
    r = rng.random()
    upper = 0.0
    for value, w in pairs:
        upper += w
        if r < upper:
            return value
    return pairs[-1][0]

def poisson(rng, lam):
    """Knuth's algorithm — avoids a numpy dependency for a simple count draw."""
    l_bound = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= l_bound:
            return k - 1

def random_amount(rng):
    return rng.choice(AMOUNT_TIERS) if rng.random() < 0.85 else round(rng.uniform(10, 150), 2)

def build_topup(customer_id, dt, status, rng):
    method = "auto_recharge" if rng.random() < 0.4 else rng.choice(METHODS)
    return {
        "customer_id": customer_id,
        "topup_datetime": dt.isoformat(sep=" "),
        "amount": random_amount(rng),
        "topup_method": method,
        "status": status,
    }

def build_customer_topups(customer_id, rng, now, avg_per_customer, is_low_balance_seed):
    rows = []
    if is_low_balance_seed:
        # Older, healthy history: 2-4 successful top-ups more than 30 days ago
        for _ in range(rng.randint(2, 4)):
            days_ago = rng.randint(31, 300)
            rows.append(build_topup(customer_id, now - timedelta(days=days_ago), "success", rng))
        # Trailing 30 days: only failed attempts, no success since
        for _ in range(rng.randint(2, 3)):
            days_ago = rng.randint(0, 29)
            rows.append(build_topup(customer_id, now - timedelta(days=days_ago), "failed", rng))
        return rows

    count = poisson(rng, avg_per_customer)
    for _ in range(count):
        days_ago = rng.randint(0, 364)
        status = weighted_choice(rng, [("success", 0.95), ("failed", 0.05)])
        rows.append(build_topup(customer_id, now - timedelta(days=days_ago), status, rng))
    return rows

HEADER = ["topup_id", "customer_id", "topup_datetime", "amount", "topup_method", "status"]

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--customers", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--avg-per-customer", type=float, default=6.0)
    p.add_argument("--low-balance-pct", type=float, default=0.08)
    p.add_argument("--seed", type=int, default=3)
    args = p.parse_args()

    rng = random.Random(args.seed)
    now = datetime(2026, 7, 13, 12, 0, 0)

    with open(args.customers, encoding="utf-8", newline="") as f:
        customers = list(csv.DictReader(f))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    total = 0
    seeded = 0
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        topup_seq = 0
        for c in customers:
            is_seed = rng.random() < args.low_balance_pct
            if is_seed:
                seeded += 1
            rows = build_customer_topups(c["customer_id"], rng, now, args.avg_per_customer, is_seed)
            for row in rows:
                topup_seq += 1
                row["topup_id"] = f"ht101_tw_topup_{topup_seq:07d}"
                writer.writerow(row)
            total += len(rows)

    print(f"Done — {total:,} top-ups across {len(customers):,} customers", file=sys.stderr)
    print(f"  seeded low-balance customers: {seeded:,} ({seeded/len(customers):.1%})", file=sys.stderr)
    print(f"Output: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
