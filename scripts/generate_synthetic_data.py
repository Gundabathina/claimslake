#!/usr/bin/env python3
"""
generate_synthetic_data.py

Generates synthetic healthcare claims data for the ClaimsLake project:
members, providers, diagnoses (reference), and claims.

ALL data produced by this script is synthetic and randomly generated.
No real patient, member, or provider information is used anywhere in
this project.

The script intentionally injects realistic data quality problems so the
downstream Bronze/Silver/Gold pipeline has real issues to detect and
handle later in the project:

  - duplicate claim submissions and duplicate member records
  - missing values (paid_amount, zip_code, specialty)
  - invalid values (negative paid_amount, unknown diagnosis codes,
    invalid state codes, an impossible date of birth)
  - late-arriving claims (large gap between service_date and submission_date)
  - a schema-drift batch (claims_batch_2.csv has an extra column,
    adjustment_amount, that claims_batch_1.csv does not have)
  - a provider "network status change" signal used later to build an
    SCD Type 2 dim_provider in the Gold layer

Usage:
    python scripts/generate_synthetic_data.py
    python scripts/generate_synthetic_data.py --members 500 --providers 80 --claims 5000
    python scripts/generate_synthetic_data.py --sample-only   # small + fast, for repo samples

Note on how this script was validated: this repository was built in an
environment without a local Python interpreter available to the tool
building it. The logic below was carefully hand-reviewed line by line,
but has NOT been executed by an automated test run as part of building
this repository. Please run it locally (pure standard library, no
dependencies beyond Python 3.8+) to generate real data and confirm
behavior before relying on it.
"""

import argparse
import csv
import os
import random
import uuid
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Reference data pools (all synthetic)
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
]

STATES = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI", "NJ", "VA", "WA", "AZ", "MA"]
INVALID_STATES = ["ZZ", "XX", "00"]

PLAN_TYPES = ["HMO", "PPO", "EPO", "POS"]

SPECIALTIES = [
    "Family Medicine", "Internal Medicine", "Cardiology", "Orthopedics",
    "Endocrinology", "Dermatology", "Psychiatry", "Pediatrics", "Radiology",
    "General Surgery", "Neurology", "Pulmonology",
]

SOURCE_SYSTEMS_MEMBER = ["ENROLLMENT_SYS_A", "ENROLLMENT_SYS_B"]
SOURCE_SYSTEMS_PROVIDER = ["PROVIDER_NETWORK_SYS"]
SOURCE_SYSTEMS_CLAIM = ["CLAIMS_SYS_A", "CLAIMS_SYS_B"]

# (diagnosis_code, description, category)
DIAGNOSES = [
    ("E11.9", "Type 2 diabetes mellitus without complications", "Endocrine"),
    ("I10", "Essential (primary) hypertension", "Circulatory"),
    ("J45.909", "Unspecified asthma, uncomplicated", "Respiratory"),
    ("M54.5", "Low back pain", "Musculoskeletal"),
    ("F41.1", "Generalized anxiety disorder", "Mental Health"),
    ("K21.9", "Gastro-esophageal reflux disease without esophagitis", "Digestive"),
    ("N39.0", "Urinary tract infection, site not specified", "Genitourinary"),
    ("S93.401A", "Sprain of ankle, initial encounter", "Injury"),
    ("R51", "Headache", "Symptoms"),
    ("E78.5", "Hyperlipidemia, unspecified", "Endocrine"),
    ("J06.9", "Acute upper respiratory infection, unspecified", "Respiratory"),
    ("M25.50", "Pain in unspecified joint", "Musculoskeletal"),
]

CLAIM_STATUSES = ["Paid", "Denied", "Pending"]
DENIAL_REASONS = [
    "Not medically necessary", "Duplicate claim", "Coverage terminated",
    "Missing prior authorization", "Out-of-network provider",
]

# Intentionally invalid/unknown diagnosis codes (not present in diagnoses.csv)
UNKNOWN_DIAGNOSIS_CODES = ["Z99.999", "Q00.0X", "UNK000"]

BASE_CLAIM_FIELDS = [
    "claim_id", "member_id", "provider_id", "diagnosis_code", "service_date",
    "submission_date", "billed_amount", "paid_amount", "claim_status",
    "denial_reason", "ingestion_batch_id", "source_system",
]


def _rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))


def generate_diagnoses():
    return [
        {"diagnosis_code": code, "diagnosis_description": desc, "category": cat}
        for code, desc, cat in DIAGNOSES
    ]


def generate_members(n):
    members = []
    for i in range(n):
        member_id = f"M{1000000 + i}"
        dob = _rand_date(date(1935, 1, 1), date(2015, 12, 31))
        enrollment_start = _rand_date(date(2019, 1, 1), date(2025, 6, 1))
        # ~15% of members are still active (no enrollment_end_date)
        enrollment_end = None if random.random() < 0.15 else _rand_date(
            enrollment_start, date(2026, 7, 1))

        state = random.choice(STATES)
        zip_code = f"{random.randint(10000, 99999)}"

        # --- inject data quality issues ---
        if random.random() < 0.03:          # ~3% missing zip
            zip_code = ""
        if random.random() < 0.02:          # ~2% invalid state code
            state = random.choice(INVALID_STATES)
        if random.random() < 0.005:         # ~0.5% impossible DOB (data entry error)
            dob = date(2031, 1, 1)

        members.append({
            "member_id": member_id,
            "first_name": random.choice(FIRST_NAMES),
            "last_name": random.choice(LAST_NAMES),
            "date_of_birth": dob.isoformat(),
            "gender": random.choice(["M", "F", "U"]),
            "enrollment_start_date": enrollment_start.isoformat(),
            "enrollment_end_date": enrollment_end.isoformat() if enrollment_end else "",
            "plan_type": random.choice(PLAN_TYPES),
            "state": state,
            "zip_code": zip_code,
            "source_system": random.choice(SOURCE_SYSTEMS_MEMBER),
        })

    # --- inject duplicate member records (simulating a re-sent enrollment file) ---
    dup_count = max(1, int(n * 0.01))
    members += [dict(m) for m in random.sample(members, dup_count)]
    random.shuffle(members)
    return members


def generate_providers(n):
    providers = []
    used_npis = set()
    for i in range(n):
        provider_id = f"P{100000 + i}"
        npi = str(random.randint(1000000000, 9999999999))
        specialty = random.choice(SPECIALTIES)

        if random.random() < 0.02:                  # ~2% missing specialty
            specialty = ""
        if random.random() < 0.01 and used_npis:    # ~1% duplicate NPI (data error)
            npi = random.choice(list(used_npis))
        used_npis.add(npi)

        providers.append({
            "provider_id": provider_id,
            "provider_name": f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "specialty": specialty,
            "npi": npi,
            "network_status": "In-Network",
            "address_state": random.choice(STATES),
            "effective_date": _rand_date(date(2018, 1, 1), date(2023, 1, 1)).isoformat(),
            "source_system": random.choice(SOURCE_SYSTEMS_PROVIDER),
        })

    # --- simulate a network status change for ~10% of providers ---
    # A second row with a later effective_date and a different network_status
    # represents the same provider_id changing status over time. The Gold-layer
    # dim_provider (SCD Type 2) is what turns this raw signal into proper
    # valid_from / valid_to / is_current history.
    change_count = max(1, int(n * 0.10))
    changed = random.sample(providers, change_count)
    for p in changed:
        new_row = dict(p)
        new_row["network_status"] = (
            "Out-of-Network" if p["network_status"] == "In-Network" else "In-Network"
        )
        new_row["effective_date"] = _rand_date(date(2023, 2, 1), date(2025, 12, 31)).isoformat()
        providers.append(new_row)

    random.shuffle(providers)
    return providers


def generate_claims(n, members, providers, diagnoses, batch="1"):
    claims = []
    member_ids = [m["member_id"] for m in members]
    provider_ids = [p["provider_id"] for p in providers]
    diagnosis_codes = [d["diagnosis_code"] for d in diagnoses]

    for _ in range(n):
        claim_id = f"C{uuid.uuid4().hex[:12].upper()}"
        service_date = _rand_date(date(2024, 1, 1), date(2026, 6, 30))

        # ~5% of claims are late-arriving (long gap between service and submission)
        if random.random() < 0.05:
            submission_date = service_date + timedelta(days=random.randint(91, 240))
        else:
            submission_date = service_date + timedelta(days=random.randint(1, 45))

        billed_amount = round(random.uniform(50, 15000), 2)
        status = random.choices(CLAIM_STATUSES, weights=[0.75, 0.15, 0.10])[0]

        if status == "Paid":
            paid_amount = round(billed_amount * random.uniform(0.4, 0.95), 2)
        elif status == "Denied":
            paid_amount = 0.0
        else:
            paid_amount = None

        diagnosis_code = random.choice(diagnosis_codes)

        # --- inject data quality issues ---
        if random.random() < 0.02:          # ~2% unknown/invalid diagnosis code
            diagnosis_code = random.choice(UNKNOWN_DIAGNOSIS_CODES)
        if status == "Paid" and random.random() < 0.03:   # ~3% missing paid_amount though Paid
            paid_amount = None
        if random.random() < 0.01:          # ~1% negative paid_amount (data entry error)
            paid_amount = -abs(paid_amount) if paid_amount else -round(random.uniform(10, 500), 2)

        denial_reason = random.choice(DENIAL_REASONS) if status == "Denied" else ""

        row = {
            "claim_id": claim_id,
            "member_id": random.choice(member_ids),
            "provider_id": random.choice(provider_ids),
            "diagnosis_code": diagnosis_code,
            "service_date": service_date.isoformat(),
            "submission_date": submission_date.isoformat(),
            "billed_amount": billed_amount,
            "paid_amount": "" if paid_amount is None else paid_amount,
            "claim_status": status,
            "denial_reason": denial_reason,
            "ingestion_batch_id": f"BATCH_{batch}",
            "source_system": random.choice(SOURCE_SYSTEMS_CLAIM),
        }

        if batch == "2":
            # --- schema drift: batch 2 introduces a column batch 1 does not have ---
            row["adjustment_amount"] = (
                round(random.uniform(0, 200), 2) if random.random() < 0.2 else ""
            )

        claims.append(row)

    # --- inject duplicate claim submissions (exact re-sent rows) ---
    dup_count = max(1, int(n * 0.015))
    claims += [dict(c) for c in random.sample(claims, dup_count)]
    random.shuffle(claims)
    return claims


def write_csv(rows, path, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic ClaimsLake source data.")
    parser.add_argument("--members", type=int, default=500)
    parser.add_argument("--providers", type=int, default=80)
    parser.add_argument("--claims", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="data/generated")
    parser.add_argument("--sample-dir", type=str, default="data/sample")
    parser.add_argument("--sample-size", type=int, default=50,
                         help="Rows per entity written to --sample-dir for the repo.")
    parser.add_argument("--sample-only", action="store_true",
                         help="Generate a small dataset directly (fast, for repo samples).")
    args = parser.parse_args()

    random.seed(args.seed)

    if args.sample_only:
        args.members, args.providers, args.claims = 60, 12, 150

    diagnoses = generate_diagnoses()
    members = generate_members(args.members)
    providers = generate_providers(args.providers)

    claims_batch_1_n = max(1, int(args.claims * 0.9))
    claims_batch_2_n = max(1, args.claims - claims_batch_1_n)
    claims_batch_1 = generate_claims(claims_batch_1_n, members, providers, diagnoses, batch="1")
    claims_batch_2 = generate_claims(claims_batch_2_n, members, providers, diagnoses, batch="2")

    member_fields = list(members[0].keys())
    provider_fields = list(providers[0].keys())
    diagnosis_fields = list(diagnoses[0].keys())
    batch2_fields = BASE_CLAIM_FIELDS + ["adjustment_amount"]

    write_csv(diagnoses, os.path.join(args.output_dir, "diagnoses.csv"), diagnosis_fields)
    write_csv(members, os.path.join(args.output_dir, "members.csv"), member_fields)
    write_csv(providers, os.path.join(args.output_dir, "providers.csv"), provider_fields)
    write_csv(claims_batch_1, os.path.join(args.output_dir, "claims_batch_1.csv"), BASE_CLAIM_FIELDS)
    write_csv(claims_batch_2, os.path.join(args.output_dir, "claims_batch_2.csv"), batch2_fields)

    write_csv(diagnoses, os.path.join(args.sample_dir, "diagnoses_sample.csv"), diagnosis_fields)
    write_csv(members[:args.sample_size], os.path.join(args.sample_dir, "members_sample.csv"), member_fields)
    write_csv(providers[:args.sample_size], os.path.join(args.sample_dir, "providers_sample.csv"), provider_fields)
    write_csv(claims_batch_1[:args.sample_size], os.path.join(args.sample_dir, "claims_batch_1_sample.csv"), BASE_CLAIM_FIELDS)
    write_csv(claims_batch_2[:args.sample_size], os.path.join(args.sample_dir, "claims_batch_2_sample.csv"), batch2_fields)

    print(f"Generated {len(diagnoses)} diagnoses -> {args.output_dir}/diagnoses.csv")
    print(f"Generated {len(members)} member rows (incl. duplicates) -> {args.output_dir}/members.csv")
    print(f"Generated {len(providers)} provider rows (incl. status-change rows) -> {args.output_dir}/providers.csv")
    print(f"Generated {len(claims_batch_1)} claims -> {args.output_dir}/claims_batch_1.csv")
    print(f"Generated {len(claims_batch_2)} claims (schema-drift batch) -> {args.output_dir}/claims_batch_2.csv")
    print(f"Sample files (first {args.sample_size} rows each) written to {args.sample_dir}/")


if __name__ == "__main__":
    main()
