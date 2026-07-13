#!/usr/bin/env python3
"""
generate_customers.py

Generates a CSV of synthetic TollWay toll-account customers, one row per
account. TollWay is a fictional AU toll-road operator built for Hightouch
101 training — not a real company. Pure stdlib; streams line-by-line.

Usage:
    python generate_customers.py --count 1000 --out out/customers.csv
    python generate_customers.py --count 1000 --out out/customers.csv --seed 7

Output file is CSV with header row. Emails use the @example.com reserved
domain (RFC 2606) so nothing can ever be delivered.
"""

import argparse
import csv
import os
import random
import sys
import time
from datetime import date, timedelta

TODAY = date(2026, 7, 13)

# ----------------------------------------------------------------------
# Name pools (reused from house style)
# ----------------------------------------------------------------------

FIRST_NAMES_F = [
    "Olivia", "Charlotte", "Amelia", "Ava", "Mia", "Isla", "Grace", "Harper",
    "Chloe", "Sophia", "Emily", "Zoe", "Matilda", "Ruby", "Willow", "Evie",
    "Sophie", "Lily", "Ella", "Hannah", "Aria", "Scarlett", "Alice", "Lucy",
    "Jane", "Sarah", "Emma", "Jessica", "Laura", "Natalie", "Holly", "Eve",
]

FIRST_NAMES_M = [
    "Oliver", "Noah", "William", "Jack", "Leo", "Henry", "Lucas", "Thomas",
    "James", "Charlie", "Liam", "Hunter", "Ethan", "Mason", "Max", "Oscar",
    "Samuel", "Archie", "Alexander", "Jacob", "Harrison", "Cooper", "Isaac",
    "Daniel", "Michael", "David", "Joshua", "Ryan", "Andrew", "Ben", "Adam",
]

FIRST_NAMES_O = ["Alex", "Jordan", "Riley", "Taylor", "Morgan", "Avery", "Quinn", "Casey"]

LAST_NAMES = [
    "Smith", "Jones", "Williams", "Brown", "Taylor", "Wilson", "Johnson",
    "White", "Martin", "Anderson", "Thompson", "Nguyen", "Thomas", "Walker",
    "Harris", "Lee", "Clark", "Lewis", "Robinson", "Hall", "Allen",
    "Young", "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson",
    "Hill", "Campbell", "Mitchell", "Roberts", "Carter", "Phillips", "Evans",
    "Turner", "Parker", "Collins", "Edwards", "Stewart", "Flores", "Morris",
    "Patel", "Singh", "Kumar", "Khan", "Kim", "Chen", "Wang", "Tran", "Le",
]

BUSINESS_SUFFIXES = [
    "Logistics", "Transport", "Freight", "Couriers", "Removals", "Haulage",
    "Distribution", "Trades", "Group",
]

# ----------------------------------------------------------------------
# Geography — AU only. Toll roads are an AU capital-city phenomenon
# (NSW/VIC/QLD), so this deliberately does NOT follow the AU/NZ 90/10
# split used by generate_customers.py in the Amperity mock-data set.
# See dictionary/inconsistencies.md for this and other documented
# deviations from house convention.
# ----------------------------------------------------------------------

NSW_CITIES = [("Sydney", "2000"), ("Newcastle", "2300"), ("Wollongong", "2500"), ("Parramatta", "2150")]
VIC_CITIES = [("Melbourne", "3000"), ("Geelong", "3220"), ("Ballarat", "3350"), ("Dandenong", "3175")]
QLD_CITIES = [("Brisbane", "4000"), ("Gold Coast", "4217"), ("Logan City", "4114"), ("Ipswich", "4305")]
OTHER_CITIES = [
    ("Perth", "WA", "6000"), ("Adelaide", "SA", "5000"), ("Hobart", "TAS", "7000"),
    ("Canberra", "ACT", "2600"), ("Darwin", "NT", "0800"),
]

TIMEZONES = {
    "NSW": "Australia/Sydney", "VIC": "Australia/Melbourne", "QLD": "Australia/Brisbane",
    "WA": "Australia/Perth", "SA": "Australia/Adelaide", "TAS": "Australia/Hobart",
    "ACT": "Australia/Sydney", "NT": "Australia/Darwin",
}

# ----------------------------------------------------------------------
# Weighted pickers
# ----------------------------------------------------------------------

def weighted_choice(rng: random.Random, pairs):
    """pairs = [(value, cumulative_probability_upper_bound), ...] ascending, last should be 1.0"""
    r = rng.random()
    for value, upper in pairs:
        if r < upper:
            return value
    return pairs[-1][0]

def pick_gender(rng): return weighted_choice(rng, [("F", 0.48), ("M", 0.96), ("O", 1.0)])
def pick_first_name(rng, gender):
    if gender == "F": return rng.choice(FIRST_NAMES_F)
    if gender == "M": return rng.choice(FIRST_NAMES_M)
    return rng.choice(FIRST_NAMES_O)

def pick_home_state(rng): return weighted_choice(rng, [("NSW", 0.45), ("VIC", 0.75), ("QLD", 0.90), ("OTHER", 1.0)])

def pick_location(rng, state):
    if state == "NSW":
        city, postal = rng.choice(NSW_CITIES)
        return "NSW", city, postal
    if state == "VIC":
        city, postal = rng.choice(VIC_CITIES)
        return "VIC", city, postal
    if state == "QLD":
        city, postal = rng.choice(QLD_CITIES)
        return "QLD", city, postal
    city, real_state, postal = rng.choice(OTHER_CITIES)
    return real_state, city, postal

def random_phone(rng): return f"+614{rng.randint(10000000, 99999999)}"

def random_dob(rng):
    years_ago = int(rng.triangular(18, 80, 40))
    days_offset = rng.randint(0, 365)
    return (TODAY - timedelta(days=years_ago * 365 + days_offset)).isoformat()

def random_signup_date(rng):
    # TollWay training data spans a synthetic 3-year signup window
    days_ago = int(rng.triangular(0, 1095, 400))
    return (TODAY - timedelta(days=days_ago)).isoformat()

def pick_account_type(rng): return weighted_choice(rng, [("etag", 0.55), ("video_tolling", 0.90), ("visitor_pass", 1.0)])
def pick_customer_segment(rng): return weighted_choice(rng, [("individual", 0.88), ("small_business", 1.0)])
def pick_loyalty_tier(rng): return weighted_choice(rng, [("bronze", 0.55), ("silver", 0.87), ("gold", 1.0)])
def pick_topup_mode(rng): return weighted_choice(rng, [("auto", 0.55), ("manual", 0.90), ("none", 1.0)])
def pick_account_status(rng): return weighted_choice(rng, [("active", 0.92), ("suspended", 0.97), ("closed", 1.0)])
def pick_email_subscribe(rng): return weighted_choice(rng, [("subscribed", 0.90), ("unsubscribed", 0.98), ("opted_in", 1.0)])

def build_row(i: int, rng: random.Random) -> dict:
    gender = pick_gender(rng)
    first_name = pick_first_name(rng, gender)
    last_name = rng.choice(LAST_NAMES)
    state_bucket = pick_home_state(rng)
    home_state, home_city, postal = pick_location(rng, state_bucket)
    email = f"{first_name.lower()}.{last_name.lower()}.{i}@example.com"

    customer_segment = pick_customer_segment(rng)
    business_name = f"{last_name} {rng.choice(BUSINESS_SUFFIXES)}" if customer_segment == "small_business" else ""

    account_type = pick_account_type(rng)
    topup_mode = pick_topup_mode(rng)
    auto_topup_threshold = rng.choice([10, 20, 30]) if topup_mode == "auto" else ""

    # e-tag / video tolling bill after the trip (small line of credit is normal);
    # visitor passes are prepaid and never go negative.
    if account_type == "visitor_pass":
        account_balance = round(rng.uniform(0, 100), 2)
    else:
        account_balance = round(rng.uniform(-50, 200), 2)

    return {
        "customer_id": f"ht101_tw_cust_{i:06d}",
        "account_type": account_type,
        "customer_segment": customer_segment,
        "business_name": business_name,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": random_phone(rng),
        "dob": random_dob(rng),
        "home_state": home_state,
        "home_city": home_city,
        "postal": postal,
        "time_zone": TIMEZONES[home_state],
        "signup_date": random_signup_date(rng),
        "account_status": pick_account_status(rng),
        "loyalty_tier": pick_loyalty_tier(rng),
        "payment_method_linked": "true" if rng.random() < 0.85 else "false",
        "topup_mode": topup_mode,
        "auto_topup_threshold": auto_topup_threshold,
        "account_balance": account_balance,
        "marketing_email_subscribe": pick_email_subscribe(rng),
        "sms_subscribe": "true" if rng.random() < 0.45 else "false",
    }

HEADER = [
    "customer_id", "account_type", "customer_segment", "business_name",
    "first_name", "last_name", "email", "phone", "dob", "home_state",
    "home_city", "postal", "time_zone", "signup_date", "account_status",
    "loyalty_tier", "payment_method_linked", "topup_mode",
    "auto_topup_threshold", "account_balance", "marketing_email_subscribe",
    "sms_subscribe",
]

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--count", type=int, required=True, help="number of customers to generate")
    p.add_argument("--out", required=True, help="output CSV path")
    p.add_argument("--seed", type=int, default=0, help="random seed (default 0 — deterministic)")
    args = p.parse_args()

    if args.count < 1:
        p.error("--count must be >= 1")

    rng = random.Random(args.seed)
    start = time.monotonic()
    progress_every = max(1, args.count // 10)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for i in range(1, args.count + 1):
            writer.writerow(build_row(i, rng))
            if i % progress_every == 0:
                elapsed = time.monotonic() - start
                print(f"  {i:>7,} / {args.count:,} customers  ·  {elapsed:5.1f}s", file=sys.stderr)

    elapsed = time.monotonic() - start
    print(f"\nDone — {args.count:,} customers · {elapsed:.1f}s", file=sys.stderr)
    print(f"customer_id range: ht101_tw_cust_{1:06d} → ht101_tw_cust_{args.count:06d}", file=sys.stderr)
    print(f"Output: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
