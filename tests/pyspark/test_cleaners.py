"""
test_cleaners.py

Tests for pyspark/src/cleaners.py. These exercise the real cleaning
functions on tiny in-memory DataFrames: blank-string to null conversion,
type casting, and claims batch canonicalization.
"""

import datetime
import decimal

from pyspark.sql import Row

from pyspark.src import cleaners


def test_blank_to_null_converts_empty_strings(spark):
    df = spark.createDataFrame([Row(a="x", b=""), Row(a="  ", b="y")])
    out = cleaners.blank_to_null(df, ["a", "b"]).collect()
    # "" and whitespace-only become null; real values are kept.
    assert out[0]["b"] is None
    assert out[0]["a"] == "x"
    assert out[1]["a"] is None
    assert out[1]["b"] == "y"


def test_ensure_columns_adds_missing_adjustment_amount(spark):
    df = spark.createDataFrame([Row(claim_id="C1")])
    out = cleaners.ensure_columns(df, ["adjustment_amount"])
    assert "adjustment_amount" in out.columns
    assert out.collect()[0]["adjustment_amount"] is None


def test_clean_members_casts_types_and_normalizes_state(spark):
    df = spark.createDataFrame([
        Row(member_id="M1", first_name="A", last_name="B",
            date_of_birth="1990-01-15", gender="f",
            enrollment_start_date="2020-01-01", enrollment_end_date="",
            plan_type="hmo", state=" ca ", zip_code="90001",
            source_system="ENROLL"),
    ])
    row = cleaners.clean_members(df).collect()[0]
    assert row["date_of_birth"] == datetime.date(1990, 1, 15)
    assert row["state"] == "CA"          # trimmed + upper-cased
    assert row["gender"] == "F"
    assert row["enrollment_end_date"] is None   # blank became null then date


def test_clean_claims_casts_money_and_dates(spark):
    df = spark.createDataFrame([
        Row(claim_id="C1", member_id="M1", provider_id="P1",
            diagnosis_code="e11", service_date="2024-01-01",
            submission_date="2024-01-10", billed_amount="200.50",
            paid_amount="", claim_status="Paid ", denial_reason="",
            ingestion_batch_id="BATCH_1", source_system="CLAIMS"),
    ])
    row = cleaners.clean_claims(df).collect()[0]
    assert row["billed_amount"] == decimal.Decimal("200.50")
    assert row["paid_amount"] is None            # blank -> null
    assert row["service_date"] == datetime.date(2024, 1, 1)
    assert row["claim_status"] == "Paid"         # trimmed, not re-cased
    assert row["diagnosis_code"] == "E11"        # upper-cased
    assert "adjustment_amount" in row.asDict()   # canonicalized in
