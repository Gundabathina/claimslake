"""
test_validators.py

Tests for pyspark/src/validators.py. Rows are built as raw strings and
run through the real cleaners first, so these exercise the full
clean -> validate -> split path (not just isolated helpers).
"""

from pyspark.sql import Row, functions as F

from pyspark.src import cleaners, validators


def _members(spark, rows):
    return cleaners.clean_members(spark.createDataFrame(rows))


def _member_row(**kw):
    base = dict(
        member_id="M1", first_name="A", last_name="B",
        date_of_birth="1990-01-01", gender="M",
        enrollment_start_date="2020-01-01", enrollment_end_date="",
        plan_type="HMO", state="CA", zip_code="90001", source_system="ENROLL",
    )
    base.update(kw)
    return Row(**base)


def test_members_invalid_state_is_quarantined(spark):
    df = _members(spark, [_member_row(member_id="M1", state="ZZ")])
    validated = validators.validate_members(df)
    valid, quarantine = validators.split_valid_quarantine(validated)
    assert valid.count() == 0
    q = quarantine.collect()[0]
    assert "invalid_state_code" in q["rejection_reason"]
    assert q["validation_timestamp"] is not None


def test_members_future_dob_is_quarantined(spark):
    df = _members(spark, [_member_row(member_id="M2", date_of_birth="2999-01-01")])
    validated = validators.validate_members(df)
    _, quarantine = validators.split_valid_quarantine(validated)
    assert "impossible_date_of_birth_future" in quarantine.collect()[0]["rejection_reason"]


def test_members_missing_zip_is_flag_not_rejection(spark):
    df = _members(spark, [_member_row(member_id="M3", zip_code="")])
    validated = validators.validate_members(df)
    valid, quarantine = validators.split_valid_quarantine(validated)
    assert quarantine.count() == 0             # missing zip is NOT a rejection
    assert valid.collect()[0]["has_missing_zip"] is True


def _claims(spark, rows):
    return cleaners.clean_claims(spark.createDataFrame(rows))


def _claim_row(**kw):
    base = dict(
        claim_id="C1", member_id="M1", provider_id="P1", diagnosis_code="E11",
        service_date="2024-01-01", submission_date="2024-01-10",
        billed_amount="100.00", paid_amount="80.00", claim_status="Paid",
        denial_reason="", ingestion_batch_id="BATCH_1", source_system="CLAIMS",
    )
    base.update(kw)
    return Row(**base)


def _dims(spark):
    m = spark.createDataFrame([Row(member_id="M1")])
    p = spark.createDataFrame([Row(provider_id="P1")])
    d = spark.createDataFrame([Row(diagnosis_code="E11")])
    return m, p, d


def test_claims_referential_integrity_and_amounts(spark):
    m, p, d = _dims(spark)
    df = _claims(spark, [
        _claim_row(claim_id="OK"),                                  # valid
        _claim_row(claim_id="BADMEM", member_id="M999"),            # orphan member
        _claim_row(claim_id="NEG", paid_amount="-5.00"),            # negative paid
        _claim_row(claim_id="NOPAID", paid_amount="", claim_status="Paid"),  # paid but no amount
    ])
    validated = validators.validate_claims(df, m, p, d)
    valid, quarantine = validators.split_valid_quarantine(validated)
    reasons = {r["claim_id"]: r["rejection_reason"] for r in quarantine.collect()}
    valid_ids = [r["claim_id"] for r in valid.collect()]
    assert valid_ids == ["OK"]
    assert "invalid_member_id_reference" in reasons["BADMEM"]
    assert "negative_paid_amount" in reasons["NEG"]
    assert "missing_paid_amount_for_paid_claim" in reasons["NOPAID"]


def test_claims_late_arriving_flag_boundary(spark):
    m, p, d = _dims(spark)
    df = _claims(spark, [
        _claim_row(claim_id="ONTIME", service_date="2024-01-01",
                   submission_date="2024-02-15"),   # 45 days -> not late
        _claim_row(claim_id="LATE", service_date="2024-01-01",
                   submission_date="2024-06-01"),    # ~152 days -> late
    ])
    validated = validators.validate_claims(df, m, p, d)
    flags = {r["claim_id"]: r["is_late_arriving"] for r in validated.collect()}
    assert flags["ONTIME"] is False
    assert flags["LATE"] is True
