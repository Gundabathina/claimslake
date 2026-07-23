"""
validators.py

Business-rule data-quality checks for the Silver layer. Each validate_*
function adds a "_rejection_reasons" array column: an empty array means
the row passes every rule and is eligible for Silver; a non-empty array
means the row is quarantined, listing every rule it failed (a row can
fail more than one rule at once).

This module also adds a few non-rejecting DATA QUALITY FLAG columns
(e.g. has_missing_zip, is_late_arriving) for rows that are valid but
worth tracking. Flags are informational only and never cause quarantine.

Nothing here mutates values to "fix" them. Silver quarantines or flags;
it does not silently correct data or invent replacement values.
"""

from typing import Tuple

from pyspark.sql import DataFrame, functions as F

from pyspark.src.schemas import (
    LATE_ARRIVING_THRESHOLD_DAYS,
    VALID_CLAIM_STATUSES,
    VALID_US_STATE_CODES,
)

REASON_COL = "_rejection_reasons"


def _reasons_array(*condition_reason_pairs):
    """Build an array<string> containing one entry per (condition,
    reason) pair whose condition is true for the row. Implemented as
    array_except(array(when...), array(null)) so only the matching
    reasons remain and non-matches drop out."""
    parts = [F.when(cond, F.lit(reason)) for cond, reason in condition_reason_pairs]
    return F.array_except(F.array(*parts), F.array(F.lit(None).cast("string")))


def split_valid_quarantine(
    df: DataFrame, reason_col: str = REASON_COL
) -> Tuple[DataFrame, DataFrame]:
    """Split a validated DataFrame into (valid_df, quarantine_df).

    valid_df: rows with no rejection reasons, reason_col dropped.
    quarantine_df: rows with at least one reason; reason_col is collapsed
    into a single 'rejection_reason' string and a 'validation_timestamp'
    is stamped, satisfying the quarantine record contract (see
    docs/data_dictionary/silver_schemas.md)."""
    valid = df.filter(F.size(F.col(reason_col)) == 0).drop(reason_col)
    quarantine = (
        df.filter(F.size(F.col(reason_col)) > 0)
        .withColumn("rejection_reason", F.concat_ws("; ", F.col(reason_col)))
        .withColumn("validation_timestamp", F.current_timestamp())
        .drop(reason_col)
    )
    return valid, quarantine


def validate_members(df: DataFrame) -> DataFrame:
    reasons = _reasons_array(
        (F.col("member_id").isNull(), "missing_member_id"),
        (~F.col("state").isin(list(VALID_US_STATE_CODES)), "invalid_state_code"),
        (F.col("date_of_birth") > F.current_date(),
         "impossible_date_of_birth_future"),
    )
    df = df.withColumn(REASON_COL, reasons)
    # Missing zip_code is documented as nullable/expected (see
    # docs/data_dictionary/source_schemas.md): flagged, never rejected.
    df = df.withColumn("has_missing_zip", F.col("zip_code").isNull())
    return df


def validate_providers(df: DataFrame) -> DataFrame:
    reasons = _reasons_array(
        (F.col("provider_id").isNull(), "missing_provider_id"),
        (~F.col("address_state").isin(list(VALID_US_STATE_CODES)),
         "invalid_address_state"),
        (F.col("effective_date").isNull(), "missing_effective_date"),
    )
    df = df.withColumn(REASON_COL, reasons)
    df = df.withColumn("has_missing_specialty", F.col("specialty").isNull())
    # A single NPI mapped to more than one provider_id is a real data
    # error, but we cannot tell which provider_id is correct from this
    # data alone, so we FLAG it for downstream investigation rather than
    # quarantine it (dropping it could remove a legitimate provider).
    npi_counts = df.groupBy("npi").agg(
        F.countDistinct("provider_id").alias("_npi_provider_count")
    )
    df = df.join(npi_counts, on="npi", how="left")
    df = df.withColumn(
        "has_duplicate_npi",
        F.when(F.col("npi").isNotNull(), F.col("_npi_provider_count") > 1)
        .otherwise(F.lit(False)),
    ).drop("_npi_provider_count")
    return df


def validate_diagnoses(df: DataFrame) -> DataFrame:
    reasons = _reasons_array(
        (F.col("diagnosis_code").isNull(), "missing_diagnosis_code"),
        (F.col("diagnosis_description").isNull(), "missing_diagnosis_description"),
        (F.col("category").isNull(), "missing_category"),
    )
    return df.withColumn(REASON_COL, reasons)


def validate_claims(
    df: DataFrame,
    valid_member_ids: DataFrame,
    valid_provider_ids: DataFrame,
    valid_diagnosis_codes: DataFrame,
) -> DataFrame:
    """Referential integrity + field-level validation for claims.

    valid_member_ids / valid_provider_ids / valid_diagnosis_codes are
    single-column DataFrames of the keys that survived into Silver for
    each dimension. They are small (at most a few thousand rows here),
    so they are BROADCAST into the join instead of triggering a shuffle
    join against the larger claims fact data - see pyspark/README.md for
    the reasoning. A left join + isNull() check is used (rather than a
    left-anti join) because we need to keep every claim and simply
    record whether each foreign key resolved."""
    df = (
        df.join(
            F.broadcast(
                valid_member_ids.withColumnRenamed("member_id", "_vm")
            ),
            df["member_id"] == F.col("_vm"), "left",
        )
        .join(
            F.broadcast(
                valid_provider_ids.withColumnRenamed("provider_id", "_vp")
            ),
            df["provider_id"] == F.col("_vp"), "left",
        )
        .join(
            F.broadcast(
                valid_diagnosis_codes.withColumnRenamed("diagnosis_code", "_vd")
            ),
            df["diagnosis_code"] == F.col("_vd"), "left",
        )
    )

    reasons = _reasons_array(
        (F.col("claim_id").isNull(), "missing_claim_id"),
        (F.col("service_date").isNull() | F.col("submission_date").isNull(),
         "invalid_or_missing_date"),
        (F.col("submission_date") < F.col("service_date"),
         "submission_before_service_date"),
        (F.col("paid_amount") < 0, "negative_paid_amount"),
        ((F.col("claim_status") == "Paid") & F.col("paid_amount").isNull(),
         "missing_paid_amount_for_paid_claim"),
        (~F.col("claim_status").isin(list(VALID_CLAIM_STATUSES)),
         "invalid_claim_status"),
        (F.col("_vm").isNull(), "invalid_member_id_reference"),
        (F.col("_vp").isNull(), "invalid_provider_id_reference"),
        (F.col("_vd").isNull(), "invalid_diagnosis_code_reference"),
    )
    df = df.withColumn(REASON_COL, reasons).drop("_vm", "_vp", "_vd")

    # Late-arriving is a FLAG, not a rejection: these are valid claims
    # that simply arrived long after the service occurred. We keep them
    # and mark them so downstream backfill/reprocessing logic can find
    # them (see docs/interview_guide/03_pyspark_silver.md).
    days_late = F.datediff(F.col("submission_date"), F.col("service_date"))
    both_dates = F.col("service_date").isNotNull() & F.col("submission_date").isNotNull()
    df = df.withColumn(
        "is_late_arriving",
        F.when(both_dates, days_late > LATE_ARRIVING_THRESHOLD_DAYS)
        .otherwise(F.lit(False)),
    ).withColumn(
        "days_late", F.when(both_dates, days_late),
    )
    return df
