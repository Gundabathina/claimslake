"""
transformations.py

Per-dataset Silver build functions. Each build_silver_* function takes a
raw Bronze DataFrame (as produced by readers.py) and returns a tuple:

    (silver_df, quarantine_df, metrics_dict)

It wires together cleaners -> validators -> deduplication in the right
order for that dataset and computes real data-quality metrics from the
actual DataFrames (every number comes from a Spark action on real data,
never a hard-coded constant).

The provider build is deliberately different from the others: it does
NOT collapse a provider's multiple network_status/effective_date rows.
Those are legitimate historical versions, preserved so the future
Gold-layer dim_provider can implement SCD Type 2. See
build_silver_providers below and docs/interview_guide/03_pyspark_silver.md.
"""

from typing import Dict, List, Tuple

from pyspark.sql import DataFrame, functions as F

from pyspark.src import cleaners, deduplication, validators

# Business columns per dataset (source columns only): used for exact
# duplicate-row detection. Bronze technical metadata (ingestion_timestamp,
# source_file, file_hash) and reader-derived columns are excluded, because
# two ingestions of the same resent file differ only in that metadata.
MEMBERS_BUSINESS_COLS = [
    "member_id", "first_name", "last_name", "date_of_birth", "gender",
    "enrollment_start_date", "enrollment_end_date", "plan_type", "state",
    "zip_code", "source_system",
]
PROVIDERS_BUSINESS_COLS = [
    "provider_id", "provider_name", "specialty", "npi", "network_status",
    "address_state", "effective_date", "source_system",
]
DIAGNOSES_BUSINESS_COLS = ["diagnosis_code", "diagnosis_description", "category"]
CLAIMS_BUSINESS_COLS = [
    "claim_id", "member_id", "provider_id", "diagnosis_code", "service_date",
    "submission_date", "billed_amount", "paid_amount", "claim_status",
    "denial_reason", "ingestion_batch_id", "source_system", "adjustment_amount",
]


def _reason_breakdown(validated_df: DataFrame, reason_col: str) -> Dict[str, int]:
    """Count how many rows failed each individual rule (a row failing two
    rules counts once under each). Computed from the reasons array before
    it is collapsed to a string."""
    exploded = validated_df.select(F.explode(F.col(reason_col)).alias("reason"))
    rows = exploded.groupBy("reason").count().collect()
    return {r["reason"]: r["count"] for r in rows}


def _null_counts(df: DataFrame, columns: List[str]) -> Dict[str, int]:
    aggs = [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in columns]
    row = df.agg(*aggs).collect()[0]
    return {c: int(row[c] or 0) for c in columns}


def build_silver_members(bronze_df: DataFrame) -> Tuple[DataFrame, DataFrame, Dict]:
    input_count = bronze_df.count()
    cleaned = cleaners.clean_members(bronze_df)
    deduped, exact_dups = deduplication.drop_exact_duplicate_rows(
        cleaned, MEMBERS_BUSINESS_COLS
    )
    validated = validators.validate_members(deduped)
    reason_breakdown = _reason_breakdown(validated, validators.REASON_COL)
    valid, quarantine = validators.split_valid_quarantine(validated)
    # Defensive: guarantee one row per member_id even for non-identical
    # same-key rows (survivor = latest enrollment, then latest ingestion).
    valid, key_dups = deduplication.deduplicate_by_key(
        valid,
        business_keys=["member_id"],
        order_by_desc_columns=["enrollment_start_date", "ingestion_timestamp"],
        tiebreak_hash_columns=MEMBERS_BUSINESS_COLS,
    )
    output_count = valid.count()
    quarantined_count = quarantine.count()
    metrics = {
        "input_count": input_count,
        "output_count": output_count,
        "exact_duplicate_rows_removed": exact_dups,
        "business_key_duplicates_removed": key_dups,
        "quarantined_count": quarantined_count,
        "quarantine_reason_breakdown": reason_breakdown,
        "missing_zip_flag_count": valid.filter(F.col("has_missing_zip")).count(),
        "null_counts": _null_counts(valid, ["date_of_birth", "state", "zip_code"]),
    }
    return valid, quarantine, metrics


def build_silver_providers(bronze_df: DataFrame) -> Tuple[DataFrame, DataFrame, Dict]:
    """IMPORTANT: providers preserves history.

    - True duplicates (byte-identical business rows, e.g. a resent feed)
      ARE collapsed via drop_exact_duplicate_rows.
    - Rows that share provider_id but differ in network_status /
      effective_date are NOT collapsed. They are legitimate historical
      versions and are the raw material the Gold SCD Type 2 dimension
      will turn into valid_from / valid_to / is_current. Collapsing them
      here would destroy that history, so we keep every distinct version.
    - The Silver grain for providers is therefore one row per
      (provider_id, effective_date) version, NOT one row per provider.
    """
    input_count = bronze_df.count()
    cleaned = cleaners.clean_providers(bronze_df)
    deduped, exact_dups = deduplication.drop_exact_duplicate_rows(
        cleaned, PROVIDERS_BUSINESS_COLS
    )
    history_providers = deduplication.count_key_groups_with_history(
        deduped, ["provider_id"]
    )
    validated = validators.validate_providers(deduped)
    reason_breakdown = _reason_breakdown(validated, validators.REASON_COL)
    valid, quarantine = validators.split_valid_quarantine(validated)
    # NOTE: no deduplicate_by_key here - preserving provider versions is
    # the whole point (future SCD Type 2).
    output_count = valid.count()
    quarantined_count = quarantine.count()
    metrics = {
        "input_count": input_count,
        "output_count": output_count,
        "exact_duplicate_rows_removed": exact_dups,
        "providers_with_historical_versions_preserved": history_providers,
        "quarantined_count": quarantined_count,
        "quarantine_reason_breakdown": reason_breakdown,
        "duplicate_npi_flag_count": valid.filter(F.col("has_duplicate_npi")).count(),
        "missing_specialty_flag_count":
            valid.filter(F.col("has_missing_specialty")).count(),
    }
    return valid, quarantine, metrics


def build_silver_diagnoses(bronze_df: DataFrame) -> Tuple[DataFrame, DataFrame, Dict]:
    input_count = bronze_df.count()
    cleaned = cleaners.clean_diagnoses(bronze_df)
    deduped, exact_dups = deduplication.drop_exact_duplicate_rows(
        cleaned, DIAGNOSES_BUSINESS_COLS
    )
    validated = validators.validate_diagnoses(deduped)
    reason_breakdown = _reason_breakdown(validated, validators.REASON_COL)
    valid, quarantine = validators.split_valid_quarantine(validated)
    valid, key_dups = deduplication.deduplicate_by_key(
        valid,
        business_keys=["diagnosis_code"],
        order_by_desc_columns=["ingestion_timestamp"],
        tiebreak_hash_columns=DIAGNOSES_BUSINESS_COLS,
    )
    metrics = {
        "input_count": input_count,
        "output_count": valid.count(),
        "exact_duplicate_rows_removed": exact_dups,
        "business_key_duplicates_removed": key_dups,
        "quarantined_count": quarantine.count(),
        "quarantine_reason_breakdown": reason_breakdown,
    }
    return valid, quarantine, metrics


def build_silver_claims(
    bronze_df: DataFrame,
    valid_member_ids: DataFrame,
    valid_provider_ids: DataFrame,
    valid_diagnosis_codes: DataFrame,
) -> Tuple[DataFrame, DataFrame, Dict]:
    input_count = bronze_df.count()
    cleaned = cleaners.clean_claims(bronze_df)
    batch1_count = cleaned.filter(F.col("ingestion_batch_id") == "BATCH_1").count()
    batch2_count = cleaned.filter(F.col("ingestion_batch_id") == "BATCH_2").count()
    deduped, exact_dups = deduplication.drop_exact_duplicate_rows(
        cleaned, CLAIMS_BUSINESS_COLS
    )
    validated = validators.validate_claims(
        deduped, valid_member_ids, valid_provider_ids, valid_diagnosis_codes
    )
    reason_breakdown = _reason_breakdown(validated, validators.REASON_COL)
    valid, quarantine = validators.split_valid_quarantine(validated)
    # One surviving row per claim_id (survivor = latest ingestion, so a
    # corrected resubmission supersedes an earlier version).
    valid, key_dups = deduplication.deduplicate_by_key(
        valid,
        business_keys=["claim_id"],
        order_by_desc_columns=["ingestion_timestamp"],
        tiebreak_hash_columns=CLAIMS_BUSINESS_COLS,
    )
    # Partition Silver claims by service month: claims analytics almost
    # always filter by a service-date range, so this enables partition
    # pruning. Year-month (not exact day) keeps the partition count and
    # file sizes sensible for this data volume.
    valid = valid.withColumn(
        "service_year_month", F.date_format(F.col("service_date"), "yyyy-MM")
    )
    late_count = valid.filter(F.col("is_late_arriving")).count()
    adjustment_non_null = valid.filter(F.col("adjustment_amount").isNotNull()).count()
    ri = {
        k: reason_breakdown.get(k, 0)
        for k in (
            "invalid_member_id_reference",
            "invalid_provider_id_reference",
            "invalid_diagnosis_code_reference",
        )
    }
    metrics = {
        "input_count": input_count,
        "output_count": valid.count(),
        "batch_1_input_rows": batch1_count,
        "batch_2_input_rows": batch2_count,
        "exact_duplicate_rows_removed": exact_dups,
        "business_key_duplicates_removed": key_dups,
        "quarantined_count": quarantine.count(),
        "quarantine_reason_breakdown": reason_breakdown,
        "referential_integrity_failures": ri,
        "negative_paid_amount_count":
            reason_breakdown.get("negative_paid_amount", 0),
        "missing_paid_amount_for_paid_claim_count":
            reason_breakdown.get("missing_paid_amount_for_paid_claim", 0),
        "late_arriving_count": late_count,
        "adjustment_amount_present_count": adjustment_non_null,
    }
    return valid, quarantine, metrics
