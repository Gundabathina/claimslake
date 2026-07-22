"""
schema_validator.py

Validates a source file's actual columns against its configured
required/expected columns, and detects schema drift (columns present in
the file but not in the canonical expected set).

This module deliberately does NOT validate business-rule data quality
(negative amounts, invalid state codes, orphaned foreign keys, etc.).
Those checks belong in the Silver layer (Milestone 3). See the
Bronze-layer design principle in ingestion/README.md: Bronze preserves
source data as faithfully as possible.
"""

from dataclasses import dataclass, field
from typing import List

from ingestion.src.config_loader import SourceConfig


@dataclass
class ValidationResult:
    status: str  # PASSED | PASSED_WITH_DRIFT | FAILED
    missing_required_columns: List[str] = field(default_factory=list)
    unexpected_columns: List[str] = field(default_factory=list)
    message: str = ""

    @property
    def passed(self) -> bool:
        return self.status in ("PASSED", "PASSED_WITH_DRIFT")


def validate_schema(actual_columns: List[str], config: SourceConfig) -> ValidationResult:
    """
    Compare actual_columns (from a real file) against the source's
    configured required_columns and expected_columns.

    Rules:
      1. Any required column missing from the file is ALWAYS a hard
         failure, regardless of schema_drift_policy. A missing required
         column means the file is structurally broken, not merely evolved.
      2. Any column present in the file but not in expected_columns is
         schema drift. What happens next depends on schema_drift_policy:
           - 'fail':  drift is a hard failure
           - 'warn':  drift is recorded and logged, ingestion proceeds
           - 'allow': drift is accepted silently, ingestion proceeds
    """
    actual_set = set(actual_columns)
    expected_set = set(config.expected_columns)
    required_set = set(config.required_columns)

    missing_required = sorted(required_set - actual_set)
    unexpected = sorted(actual_set - expected_set)

    if missing_required:
        return ValidationResult(
            status="FAILED",
            missing_required_columns=missing_required,
            unexpected_columns=unexpected,
            message="Missing required column(s): %s" % missing_required,
        )

    if unexpected:
        if config.schema_drift_policy == "fail":
            return ValidationResult(
                status="FAILED",
                unexpected_columns=unexpected,
                message="Schema drift detected and policy is 'fail': "
                        "unexpected column(s) %s" % unexpected,
            )
        if config.schema_drift_policy == "warn":
            return ValidationResult(
                status="PASSED_WITH_DRIFT",
                unexpected_columns=unexpected,
                message="Schema drift detected (policy='warn'): unexpected "
                        "column(s) %s. Proceeding." % unexpected,
            )
        # policy == 'allow'
        return ValidationResult(
            status="PASSED_WITH_DRIFT",
            unexpected_columns=unexpected,
            message="Schema drift accepted (policy='allow'): unexpected "
                    "column(s) %s." % unexpected,
        )

    return ValidationResult(
        status="PASSED",
        message="Schema matches expected columns exactly.",
    )
