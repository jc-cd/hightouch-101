#!/usr/bin/env python3
"""
generate_vehicles.py

Generates a CSV of vehicles registered against TollWay customer accounts.
Reads an existing customers CSV (from generate_customers.py) and keys
vehicle counts off customer_segment: individual accounts have 1 vehicle
(rarely 2), small_business accounts have a small fleet (2-8). Pure
stdlib; streams line-by-line.

Usage:
    python generate_vehicles.py --customers out/customers.csv --out out/vehicles.csv
    python generate_vehicles.py --customers out/customers.csv --out out/vehicles.csv --seed 2
"""

import argparse
import csv
import os
import random
import sys
from datetime import date, timedelta

TODAY = date(2026, 7, 13)

VEHICLE_TYPE_PAIRS = [("car", 0.70), ("suv", 0.90), ("motorcycle", 0.95), ("light_truck", 0.99), ("heavy_truck", 1.0)]

TAG_TYPE_BY_ACCOUNT = {
    "etag": "etag_transponder",
    "video_tolling": "video_matched",
    "visitor_pass": "none",
}

def weighted_choice(rng, pairs):
    r = rng.random()
    for value, upper in pairs:
        if r < upper:
            return value
    return pairs[-1][0]

def random_rego(rng, state):
    letters = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(3))
    digits = "".join(rng.choice("0123456789") for _ in range(2 if state in ("NSW", "VIC") else 3))
    return f"{letters}{digits}"

def vehicle_count(rng, customer_segment):
    if customer_segment == "small_business":
        return int(rng.triangular(2, 8, 3))
    return 2 if rng.random() < 0.08 else 1

def build_rows(customer, rng):
    account_type = customer["account_type"]
    tag_type = TAG_TYPE_BY_ACCOUNT[account_type]
    n = vehicle_count(rng, customer["customer_segment"])
    rows = []
    for v in range(1, n + 1):
        days_ago = int(rng.triangular(0, 1095, 300))
        rows.append({
            "vehicle_id": f"ht101_tw_veh_{customer['customer_id'][-6:]}_{v:02d}",
            "customer_id": customer["customer_id"],
            "rego_plate": random_rego(rng, customer["home_state"]),
            "state_registered": customer["home_state"],
            "vehicle_type": weighted_choice(rng, VEHICLE_TYPE_PAIRS),
            "tag_type": tag_type,
            "date_added": (TODAY - timedelta(days=days_ago)).isoformat(),
            "is_active": "true" if rng.random() < 0.95 else "false",
        })
    return rows

HEADER = ["vehicle_id", "customer_id", "rego_plate", "state_registered", "vehicle_type", "tag_type", "date_added", "is_active"]

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--customers", required=True, help="path to customers.csv from generate_customers.py")
    p.add_argument("--out", required=True, help="output CSV path")
    p.add_argument("--seed", type=int, default=2, help="random seed (default 2)")
    args = p.parse_args()

    rng = random.Random(args.seed)

    with open(args.customers, encoding="utf-8", newline="") as f:
        customers = list(csv.DictReader(f))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    total = 0
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for customer in customers:
            rows = build_rows(customer, rng)
            for row in rows:
                writer.writerow(row)
            total += len(rows)

    print(f"Done — {total:,} vehicles across {len(customers):,} customers", file=sys.stderr)
    print(f"Output: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
