#!/usr/bin/env python3
"""
generate_trips.py

Generates a fixed-size CSV of TollWay toll-gantry charge events (one row
per gantry passed, matching how real toll operators bill). Reads
customers.csv, vehicles.csv, and the hand-authored gantries.csv, and
distributes an exact total trip count unevenly across customers:

  - ~12% of customers get exactly zero trips (new signups, closed/
    suspended accounts, occasional visitor-pass users).
  - The rest draw a weight from a loyalty-tier-scaled Gamma distribution
    (gold accounts skew toward far more trips than bronze — mirrors
    real fleet/frequent-traveller behavior), then every trip row is
    assigned to a customer via a weighted lottery over those weights.

This guarantees the total is exactly --count (a pure per-customer
Poisson draw can't do that) while still producing a realistic
long-tail skew rather than a uniform spread. Pure stdlib; keeps all
rows in memory (10K rows is trivial) then writes once.

Usage:
    python generate_trips.py --customers out/customers.csv --vehicles out/vehicles.csv \
        --gantries seed-data/gantries.csv --count 10000 --out out/trips.csv
"""

import argparse
import csv
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta

TIER_GAMMA_PARAMS = {
    "bronze": (1.5, 2.0),
    "silver": (3.0, 5.0),
    "gold": (5.0, 15.0),
}

ZERO_TRIP_PCT = 0.12
HOME_STATE_TRIP_PCT = 0.75  # probability a trip's gantry is in the customer's home state

VEHICLE_CLASS_BY_TYPE = {
    "car": "light", "suv": "light", "motorcycle": "light",
    "light_truck": "heavy", "heavy_truck": "heavy",
}
CLASS_MULTIPLIER = {"light": 1.0, "heavy": 2.5}

PEAK_BANDS = [
    ("am_peak", 7, 9, 0.40),
    ("pm_peak", 16, 18, 0.40),
    ("off_peak", 0, 23, 0.20),
]

def weighted_choice(rng, pairs):
    r = rng.random()
    upper = 0.0
    for value, w in pairs:
        upper += w
        if r < upper:
            return value
    return pairs[-1][0]

def customer_weight(rng, loyalty_tier):
    if rng.random() < ZERO_TRIP_PCT:
        return 0.0
    shape, scale = TIER_GAMMA_PARAMS[loyalty_tier]
    return rng.gammavariate(shape, scale)

def random_trip_datetime(rng, now):
    days_ago = rng.randint(0, 364)
    band = weighted_choice(rng, [(b[0], b[3]) for b in PEAK_BANDS])
    lo, hi = next((b[1], b[2]) for b in PEAK_BANDS if b[0] == band)
    hour = rng.randint(lo, hi)
    minute = rng.randint(0, 59)
    day = now - timedelta(days=days_ago)
    return day.replace(hour=hour, minute=minute, second=rng.randint(0, 59), microsecond=0)

def pick_gantry(rng, gantries_by_state, gantries_all, home_state):
    if rng.random() < HOME_STATE_TRIP_PCT and gantries_by_state.get(home_state):
        return rng.choice(gantries_by_state[home_state])
    return rng.choice(gantries_all)

def load_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

HEADER = ["trip_id", "customer_id", "vehicle_id", "gantry_id", "trip_datetime",
           "distance_km", "vehicle_class", "toll_amount", "payment_status"]

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--customers", required=True)
    p.add_argument("--vehicles", required=True)
    p.add_argument("--gantries", required=True)
    p.add_argument("--count", type=int, default=10000)
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()

    rng = random.Random(args.seed)
    now = datetime(2026, 7, 13, 12, 0, 0)

    customers = load_csv(args.customers)
    vehicles = load_csv(args.vehicles)
    gantries = load_csv(args.gantries)

    vehicles_by_customer = defaultdict(list)
    for v in vehicles:
        vehicles_by_customer[v["customer_id"]].append(v)

    gantries_by_state = defaultdict(list)
    for g in gantries:
        gantries_by_state[g["state"]].append(g)

    customer_ids = [c["customer_id"] for c in customers]
    weights = [customer_weight(rng, c["loyalty_tier"]) for c in customers]
    zero_trip_count = sum(1 for w in weights if w == 0.0)

    chosen = rng.choices(customer_ids, weights=weights, k=args.count)

    customers_by_id = {c["customer_id"]: c for c in customers}

    rows = []
    for i, customer_id in enumerate(chosen, start=1):
        customer = customers_by_id[customer_id]
        candidate_vehicles = vehicles_by_customer.get(customer_id)
        vehicle = rng.choice(candidate_vehicles)
        gantry = pick_gantry(rng, gantries_by_state, gantries, customer["home_state"])

        vehicle_class = VEHICLE_CLASS_BY_TYPE.get(vehicle["vehicle_type"], "light")
        distance_km = round(rng.uniform(2, 15), 2)
        base_rate = float(gantry["base_rate_per_km"])
        toll_amount = round(distance_km * base_rate * CLASS_MULTIPLIER[vehicle_class], 2)
        payment_status = weighted_choice(rng, [("charged", 0.92), ("pending", 0.05), ("failed", 0.03)])

        rows.append({
            "trip_id": f"ht101_tw_trip_{i:07d}",
            "customer_id": customer_id,
            "vehicle_id": vehicle["vehicle_id"],
            "gantry_id": gantry["gantry_id"],
            "trip_datetime": random_trip_datetime(rng, now).isoformat(sep=" "),
            "distance_km": distance_km,
            "vehicle_class": vehicle_class,
            "toll_amount": toll_amount,
            "payment_status": payment_status,
        })

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done — {len(rows):,} trips across {len(customers):,} customers", file=sys.stderr)
    print(f"  zero-trip customers: {zero_trip_count:,} ({zero_trip_count/len(customers):.1%})", file=sys.stderr)
    print(f"Output: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
