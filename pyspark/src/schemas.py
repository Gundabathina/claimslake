"""
schemas.py

Explicit schemas and shared constants for the Silver layer.

Why explicit schemas instead of letting Spark infer them:
  1. The Bronze ingestion engine (see ingestion/src/file_reader.py) reads
     every source file with Python's csv.DictReader and writes the
     resulting strings straight to Parquet via pandas. Every Bronze
     column - including billed_amount, paid_amount, and every date - is
     therefore stored as a raw string. There is no numeric or date type
     to infer; inference would either guess wrong or require Spark to
     scan the whole file first, which is slow and still not guaranteed
     correct for a mixed-quality source.
  2. Explicit schemas make the Bronze to Silver contract visible in
     code: anyone reading this file can see exactly what Bronze provides
     without running the pipeline.
  3. Explicit schemas fail fast and loudly if a Bronze file's structure
     changes unexpectedly, instead of silently producing nulls or the
     wrong type far downstream.

Every Bronze schema below is intentionally all-string, matching what the
ingestion layer actually writes. Casting to real types (dates, decimals)
happens in cleaners.py, in the Silver layer, not here.
"""

from pyspark.sql.types import StringType, StructField, StructType


def _all_string_schema(columns):
    return StructType([StructField(c, StringType(), True) for c in columns])


BRONZE_TECHNICAL_COLUMNS = ["ingestion_timestamp", "source_file", "file_hash"]

BRONZE_MEMBERS_COLUMNS = [
    "member_id", "first_name", "last_name", "date_of_birth", "gender",
    "enrollment_start_date", "enrollment_end_date", "plan_type", "state",
    "zip_code", "source_system",
] + BRONZE_TECHNICAL_COLUMNS

BRONZE_PROVIDERS_COLUMNS = [
    "provider_id", "provider_name", "specialty", "npi", "network_status",
    "address_state", "effective_date", "source_system",
] + BRONZE_TECHNICAL_COLUMNS

BRONZE_DIAGNOSES_COLUMNS = [
    "diagnosis_code", "diagnosis_description", "category",
] + BRONZE_TECHNICAL_COLUMNS

# claims_batch_2.csv adds adjustment_amount (schema drift, handled by the
# ingestion layer's "warn" policy - see ingestion/config/sources.yaml).
# claims_batch_1.csv does not have this column. The Silver reader merges
# both files' schemas (see readers.py) so this list is the canonical
# superset; batch_1 rows simply get a null adjustment_amount once merged.
BRONZE_CLAIMS_COLUMNS = [
    "claim_id", "member_id", "provider_id", "diagnosis_code", "service_date",
    "submission_date", "billed_amount", "paid_amount", "claim_status",
    "denial_reason", "ingestion_batch_id", "source_system", "adjustment_amount",
] + BRONZE_TECHNICAL_COLUMNS

BRONZE_MEMBERS_SCHEMA = _all_string_schema(BRONZE_MEMBERS_COLUMNS)
BRONZE_PROVIDERS_SCHEMA = _all_string_schema(BRONZE_PROVIDERS_COLUMNS)
BRONZE_DIAGNOSES_SCHEMA = _all_string_schema(BRONZE_DIAGNOSES_COLUMNS)
# Not used directly as a read schema (claims uses mergeSchema across
# batch files instead - see readers.py) but kept as the documented
# canonical column superset used by cleaners.ensure_columns().
BRONZE_CLAIMS_CANONICAL_COLUMNS = BRONZE_CLAIMS_COLUMNS

# Two-letter USPS state codes plus DC. Standard public reference data
# (not invented) used to validate members.state and
# providers.address_state.
VALID_US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC",
}

VALID_CLAIM_STATUSES = {"Paid", "Denied", "Pending"}

# A claim is treated as late-arriving when the gap between service and
# submission exceeds this many days. The synthetic generator's normal
# gap is 1-45 days; the injected late-arriving cohort is 91-240 days
# (see docs/data_dictionary/source_schemas.md), so 45 cleanly separates
# the two populations without being an arbitrary guess.
LATE_ARRIVING_THRESHOLD_DAYS = 45
