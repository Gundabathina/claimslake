"""
test_silver_pipeline.py

Integration-style tests that run the real per-dataset Silver builders
(spark_jobs/src/transformations.py) against small in-memory Bronze
DataFrames, plus one end-to-end reader test that writes two claims
Parquet batches with different schemas and reads them back to prove
schema normalization works. No mocking of the transformation logic.
"""

import os

import pandas as pd
from pyspark.sql import Row

from spark_jobs.src import cleaners, transformations
from spark_jobs.src.readers import read_incremental_source

TS1 = "2024-01-01T00:00:00+00:00"
TS2 = "2024-05-01T00:00:00+00:00"


def _member(**kw):
    base = dict(
        member_id="M1", first_name="A", last_name="B",
        date_of_birth="1990-01-01", gender="M",
        enrollment_start_date="2020-01-01", enrollment_end_date="",
        plan_type="HMO", state="CA", zip_code="90001", source_system="ENROLL",
        ingestion_timestamp=TS1, source_file="members.csv", file_hash="h1",
    )
    base.update(kw)
    return Row(**base)


def test_build_silver_members_dedup_and_quarantine(spark):
    df = spark.createDataFrame([
        _member(member_id="M1"),
        _member(member_id="M1"),                       # exact duplicate row
        _member(member_id="M2", state="ZZ"),           # invalid state -> quarantine
        _member(member_id="M3", zip_code=""),          # missing zip -> valid + flag
    ])
    valid, quarantine, metrics = transformations.build_silver_members(df)
    valid_ids = sorted(r["member_id"] for r in valid.collect())
    assert metrics["exact_duplicate_rows_removed"] == 1
    assert metrics["quarantined_count"] == 1
    assert valid_ids == ["M1", "M3"]
    assert metrics["missing_zip_flag_count"] == 1


def _provider(**kw):
    base = dict(
        provider_id="P1", provider_name="Clinic", specialty="Cardiology",
        npi="1234567890", network_status="In-Network", address_state="CA",
        effective_date="2020-01-01", source_system="PROV",
        ingestion_timestamp=TS1, source_file="providers.csv", file_hash="h1",
    )
    base.update(kw)
    return Row(**base)


def test_build_silver_providers_preserves_history(spark):
    df = spark.createDataFrame([
        _provider(provider_id="P1", network_status="In-Network",
                  effective_date="2020-01-01"),
        _provider(provider_id="P1", network_status="In-Network",
                  effective_date="2020-01-01"),         # exact duplicate -> removed
        _provider(provider_id="P1", network_status="Out-of-Network",
                  effective_date="2022-06-01"),         # real change -> PRESERVED
        _provider(provider_id="P2", network_status="In-Network",
                  effective_date="2021-01-01"),
    ])
    valid, quarantine, metrics = transformations.build_silver_providers(df)
    p1_rows = [r for r in valid.collect() if r["provider_id"] == "P1"]
    assert metrics["exact_duplicate_rows_removed"] == 1
    # Both distinct P1 versions survive - history is NOT collapsed.
    assert len(p1_rows) == 2
    assert metrics["providers_with_historical_versions_preserved"] == 1


def _claim(**kw):
    base = dict(
        claim_id="C1", member_id="M1", provider_id="P1", diagnosis_code="E11",
        service_date="2024-01-01", submission_date="2024-01-10",
        billed_amount="100.00", paid_amount="80.00", claim_status="Paid",
        denial_reason="", ingestion_batch_id="BATCH_1", source_system="CLAIMS",
        adjustment_amount=None,
        ingestion_timestamp=TS1, source_file="claims_batch_1.csv", file_hash="h1",
    )
    base.update(kw)
    return Row(**base)


def test_build_silver_claims_end_to_end(spark):
    members = spark.createDataFrame([Row(member_id="M1")])
    providers = spark.createDataFrame([Row(provider_id="P1")])
    diagnoses = spark.createDataFrame([Row(diagnosis_code="E11")])
    df = spark.createDataFrame([
        _claim(claim_id="OK"),
        _claim(claim_id="OK", ingestion_timestamp=TS2),       # dup claim_id -> keep latest
        _claim(claim_id="ORPHAN", diagnosis_code="Z99"),      # bad diagnosis FK
        _claim(claim_id="LATE", service_date="2024-01-01",
               submission_date="2024-06-01"),                 # late arriving (valid)
    ])
    valid, quarantine, metrics = transformations.build_silver_claims(
        df, members, providers, diagnoses
    )
    valid_ids = sorted(r["claim_id"] for r in valid.collect())
    assert valid_ids == ["LATE", "OK"]
    assert metrics["business_key_duplicates_removed"] == 1
    assert metrics["referential_integrity_failures"]["invalid_diagnosis_code_reference"] == 1
    assert metrics["late_arriving_count"] == 1
    assert "service_year_month" in valid.columns


def test_claims_schema_normalization_across_batches(spark, tmp_path):
    # Write batch_1 WITHOUT adjustment_amount and batch_2 WITH it, into
    # Bronze-style ingestion_date partitions, then read via mergeSchema.
    root = str(tmp_path)
    part = os.path.join(root, "claims", "ingestion_date=2024-01-01")
    os.makedirs(part, exist_ok=True)
    common = dict(
        claim_id=["C1"], member_id=["M1"], provider_id=["P1"],
        diagnosis_code=["E11"], service_date=["2024-01-01"],
        submission_date=["2024-01-10"], billed_amount=["100.00"],
        paid_amount=["80.00"], claim_status=["Paid"], denial_reason=[""],
        source_system=["CLAIMS"], ingestion_timestamp=["2024-01-01T00:00:00+00:00"],
        source_file=["claims_batch_1.csv"], file_hash=["h1"],
    )
    b1 = dict(common)
    b1["ingestion_batch_id"] = ["BATCH_1"]
    pd.DataFrame(b1).to_parquet(os.path.join(part, "claims_batch_1.parquet"),
                                index=False)
    b2 = dict(common)
    b2["claim_id"] = ["C2"]
    b2["ingestion_batch_id"] = ["BATCH_2"]
    b2["source_file"] = ["claims_batch_2.csv"]
    b2["adjustment_amount"] = ["12.50"]     # only batch_2 has this column
    pd.DataFrame(b2).to_parquet(os.path.join(part, "claims_batch_2.parquet"),
                                index=False)

    df = cleaners.clean_claims(read_incremental_source(spark, root, "claims"))
    rows = {r["claim_id"]: r for r in df.collect()}
    assert "adjustment_amount" in df.columns
    assert rows["C1"]["adjustment_amount"] is None      # batch_1 -> null
    assert str(rows["C2"]["adjustment_amount"]) == "12.50"
