"""
cleaners.py

Type casting and standardization from Bronze's all-string columns to
proper Silver types. No business-rule validation happens here (that is
validators.py) and no records are dropped here - cleaning only reshapes
values, it does not decide what is valid or invent corrected values.
"""

from pyspark.sql import DataFrame, functions as F
from pyspark.sql.types import DecimalType

MONEY_TYPE = DecimalType(12, 2)
DATE_FORMAT = "yyyy-MM-dd"


def blank_to_null(df: DataFrame, columns) -> DataFrame:
    """CSV source files represent a missing value as an empty string,
    not a true NULL (csv.DictReader never produces None for a present
    column - see ingestion/src/file_reader.py). Converting "" to NULL
    before casting is what makes cast(DateType)/cast(DecimalType) behave
    correctly and what makes later isNull() checks meaningful."""
    result = df
    for c in columns:
        result = result.withColumn(
            c, F.when(F.trim(F.col(c)) == "", None).otherwise(F.col(c))
        )
    return result


def trim_upper(df: DataFrame, columns) -> DataFrame:
    """Trim whitespace and upper-case short categorical/code columns.
    The synthetic generator emits these consistently, but a real source
    system would not guarantee casing/spacing, so we normalize before
    joining or comparing (e.g. state codes, claim_status)."""
    result = df
    for c in columns:
        result = result.withColumn(c, F.upper(F.trim(F.col(c))))
    return result


def ensure_columns(df: DataFrame, columns, default=None) -> DataFrame:
    """Guarantee every column in 'columns' exists on df, adding it as a
    typed null literal if missing. Used to canonicalize claims_batch_1
    (no adjustment_amount) onto the same schema as claims_batch_2 (has
    adjustment_amount) without inventing a value for the missing
    column."""
    result = df
    for c in columns:
        if c not in result.columns:
            result = result.withColumn(c, F.lit(default))
    return result


def clean_members(df: DataFrame) -> DataFrame:
    df = blank_to_null(df, [
        "member_id", "first_name", "last_name", "date_of_birth", "gender",
        "enrollment_start_date", "enrollment_end_date", "plan_type", "state",
        "zip_code", "source_system",
    ])
    df = trim_upper(df, ["state", "gender", "plan_type"])
    df = (
        df.withColumn("date_of_birth", F.to_date("date_of_birth", DATE_FORMAT))
        .withColumn("enrollment_start_date",
                    F.to_date("enrollment_start_date", DATE_FORMAT))
        .withColumn("enrollment_end_date",
                    F.to_date("enrollment_end_date", DATE_FORMAT))
        .withColumn("zip_code", F.trim(F.col("zip_code")))
    )
    return df


def clean_providers(df: DataFrame) -> DataFrame:
    df = blank_to_null(df, [
        "provider_id", "provider_name", "specialty", "npi", "network_status",
        "address_state", "effective_date", "source_system",
    ])
    df = trim_upper(df, ["address_state", "network_status"])
    df = df.withColumn("specialty", F.trim(F.col("specialty")))
    df = df.withColumn("effective_date", F.to_date("effective_date", DATE_FORMAT))
    return df


def clean_diagnoses(df: DataFrame) -> DataFrame:
    df = blank_to_null(df, ["diagnosis_code", "diagnosis_description", "category"])
    df = trim_upper(df, ["diagnosis_code"])
    df = df.withColumn("diagnosis_description", F.trim(F.col("diagnosis_description")))
    df = df.withColumn("category", F.trim(F.col("category")))
    return df


def clean_claims(df: DataFrame) -> DataFrame:
    # Make sure the drift column exists even for batch_1-only inputs so
    # every downstream step can reference it unconditionally.
    df = ensure_columns(df, ["adjustment_amount"])
    df = blank_to_null(df, [
        "claim_id", "member_id", "provider_id", "diagnosis_code",
        "service_date", "submission_date", "billed_amount", "paid_amount",
        "claim_status", "denial_reason", "ingestion_batch_id",
        "source_system", "adjustment_amount",
    ])
    df = trim_upper(df, ["diagnosis_code"])
    # claim_status is title-case in the source (Paid/Denied/Pending); trim
    # only, so it still matches VALID_CLAIM_STATUSES without re-casing.
    df = df.withColumn("claim_status", F.trim(F.col("claim_status")))
    df = (
        df.withColumn("service_date", F.to_date("service_date", DATE_FORMAT))
        .withColumn("submission_date", F.to_date("submission_date", DATE_FORMAT))
        .withColumn("billed_amount", F.col("billed_amount").cast(MONEY_TYPE))
        .withColumn("paid_amount", F.col("paid_amount").cast(MONEY_TYPE))
        .withColumn("adjustment_amount", F.col("adjustment_amount").cast(MONEY_TYPE))
    )
    return df
