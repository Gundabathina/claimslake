"""
Tests for ingestion/src/schema_validator.py
"""

from ingestion.src.config_loader import SourceConfig
from ingestion.src.schema_validator import validate_schema


def _config(schema_drift_policy="fail"):
    return SourceConfig(
        name="claims",
        description="test",
        source_dir="data/sample",
        file_pattern="claims_batch_*.csv",
        file_format="csv",
        load_type="incremental",
        primary_key=["claim_id"],
        expected_columns=["claim_id", "member_id", "billed_amount"],
        required_columns=["claim_id", "member_id"],
        schema_drift_policy=schema_drift_policy,
        incremental_key="file",
        bronze_path="bronze/claims",
    )


def test_passes_with_exact_match():
    result = validate_schema(["claim_id", "member_id", "billed_amount"], _config())
    assert result.status == "PASSED"
    assert result.passed


def test_fails_on_missing_required_column():
    result = validate_schema(["claim_id", "billed_amount"], _config())
    assert result.status == "FAILED"
    assert "member_id" in result.missing_required_columns
    assert not result.passed


def test_drift_fails_when_policy_is_fail():
    result = validate_schema(
        ["claim_id", "member_id", "billed_amount", "adjustment_amount"],
        _config("fail"),
    )
    assert result.status == "FAILED"
    assert "adjustment_amount" in result.unexpected_columns


def test_drift_warns_when_policy_is_warn():
    result = validate_schema(
        ["claim_id", "member_id", "billed_amount", "adjustment_amount"],
        _config("warn"),
    )
    assert result.status == "PASSED_WITH_DRIFT"
    assert result.passed
    assert "adjustment_amount" in result.unexpected_columns


def test_drift_allowed_when_policy_is_allow():
    result = validate_schema(
        ["claim_id", "member_id", "billed_amount", "adjustment_amount"],
        _config("allow"),
    )
    assert result.status == "PASSED_WITH_DRIFT"
    assert result.passed


def test_missing_required_fails_even_with_allow_policy():
    result = validate_schema(["claim_id"], _config("allow"))
    assert result.status == "FAILED"
    assert "member_id" in result.missing_required_columns
