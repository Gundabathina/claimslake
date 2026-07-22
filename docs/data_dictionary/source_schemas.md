# Source Data Dictionary — ClaimsLake

All data described here is **synthetic**, produced by `scripts/generate_synthetic_data.py`. No real patient, member, or provider data is used. This document covers the raw *source* schemas (what ingestion receives before any cleaning). Silver and Gold schemas are documented separately once those layers are built (Milestones 3–4).

## Entity relationships

```
members (1) ----< claims >---- (1) providers
                     |
                     v
                diagnoses (reference / lookup)
```

- One member can have many claims (1:N)
- One provider can have many claims (1:N)
- Each claim references exactly one diagnosis code (N:1), though some reference codes that don't exist in the diagnoses table — intentionally, to simulate a real referential-integrity problem the Silver layer must catch.

## members.csv

| Column | Type | Nullable | Description |
|---|---|---|---|
| member_id | string (PK) | No | Unique member identifier, format `M#######` |
| first_name | string | No | Synthetic first name |
| last_name | string | No | Synthetic last name |
| date_of_birth | date | No | Member date of birth |
| gender | string | No | One of M / F / U |
| enrollment_start_date | date | No | Date coverage began |
| enrollment_end_date | date | Yes | Date coverage ended; blank means still active |
| plan_type | string | No | HMO / PPO / EPO / POS |
| state | string | No | Two-letter state code |
| zip_code | string | Yes (injected) | 5-digit ZIP |
| source_system | string | No | Originating enrollment system |

**Intentional data quality issues:** ~3% missing `zip_code`, ~2% invalid `state` codes, ~0.5% impossible `date_of_birth` (future date), and ~1% exact duplicate rows (simulating a re-sent enrollment file).

## providers.csv

| Column | Type | Nullable | Description |
|---|---|---|---|
| provider_id | string (PK) | No | Unique provider identifier, format `P######` |
| provider_name | string | No | Synthetic provider name |
| specialty | string | Yes (injected) | Medical specialty |
| npi | string | No | 10-digit National Provider Identifier |
| network_status | string | No | In-Network / Out-of-Network |
| address_state | string | No | Two-letter state code |
| effective_date | date | No | Date this version of the provider record became effective |
| source_system | string | No | Originating provider network system |

**Intentional data quality issues:** ~2% missing `specialty`, ~1% duplicate `npi` values across different `provider_id`s (a real-world data error), and ~10% of providers appear **twice** with different `network_status` and `effective_date` values — this simulates the raw change-over-time feed that the Gold-layer `dim_provider` (SCD Type 2) is built to properly model with `valid_from`/`valid_to`/`is_current`.

## diagnoses.csv (reference table)

| Column | Type | Nullable | Description |
|---|---|---|---|
| diagnosis_code | string (PK) | No | ICD-10-style diagnosis code |
| diagnosis_description | string | No | Human-readable description |
| category | string | No | High-level clinical category |

This is a small, static lookup table (~12 codes) covering common categories (endocrine, circulatory, respiratory, etc.) — enough to demonstrate referential integrity checks without needing the full ~70,000-code ICD-10 set.

## claims.csv (claims_batch_1.csv / claims_batch_2.csv)

| Column | Type | Nullable | Description |
|---|---|---|---|
| claim_id | string (PK) | No | Unique claim identifier |
| member_id | string (FK -> members) | No | Member the claim belongs to |
| provider_id | string (FK -> providers) | No | Provider who submitted the claim |
| diagnosis_code | string (FK -> diagnoses) | No | Diagnosis billed; occasionally invalid (injected) |
| service_date | date | No | Date service was provided |
| submission_date | date | No | Date claim was submitted for adjudication |
| billed_amount | decimal | No | Amount billed by the provider |
| paid_amount | decimal | Yes (injected) | Amount paid; blank if Pending or missing (injected) |
| claim_status | string | No | Paid / Denied / Pending |
| denial_reason | string | Yes | Populated only when claim_status = Denied |
| ingestion_batch_id | string | No | BATCH_1 or BATCH_2 |
| source_system | string | No | Originating claims system |
| adjustment_amount | decimal | Yes | **Only present in claims_batch_2.csv** — a deliberate schema-drift example |

**Intentional data quality issues:**

- ~1.5% exact duplicate claim rows (simulating duplicate submission)
- ~3% of `Paid` claims missing `paid_amount`
- ~1% negative `paid_amount` (data entry error)
- ~2% reference an unknown/invalid `diagnosis_code` not present in `diagnoses.csv`
- ~5% are **late-arriving**: `submission_date` is 91–240 days after `service_date`, versus the normal 1–45 day gap
- `claims_batch_2.csv` introduces a new `adjustment_amount` column not present in `claims_batch_1.csv` — a realistic schema-evolution scenario the ingestion/Bronze layer must handle gracefully

## Why these specific issues

Each injected problem maps directly to a real data engineering concern that later milestones must handle: duplicates require deduplication logic (Milestone 3, PySpark window functions), missing/invalid values require validation and quarantine rules (Milestone 3), late-arriving data requires a reprocessing/backfill strategy (documented in `docs/architecture`), and the schema-drift batch requires the ingestion layer to merge schemas safely rather than fail (Milestone 2).
