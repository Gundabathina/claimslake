"""
Integration-style tests for ingestion/src/ingestion_engine.py

These tests build small, temporary source directories and Bronze output
directories, then run the real ingestion engine functions against them
(no mocking of the ingestion logic itself). Only the metadata database
location is redirected to a temp file so tests stay isolated.

Requires pandas + pyarrow (see requirements.txt) because the engine writes
Bronze output as Parquet.
"""

import pandas as pd
import pytest

from ingestion.src.config_loader import SourceConfig
from ingestion.src.ingestion_engine import ingest_source
from ingestion.src.metadata_tracker import MetadataTracker


def _members_config(tmp_path, schema_drift_policy="fail"):
    return SourceConfig(
        name="members",
        description="test members source",
        source_dir=str(tmp_path / "source"),
        file_pattern="members*.csv",
        file_format="csv",
        load_type="full",
        primary_key=["member_id"],
        expected_columns=["member_id", "first_name"],
        required_columns=["member_id", "first_name"],
        schema_drift_policy=schema_drift_policy,
        incremental_key=None,
        bronze_path=str(tmp_path / "bronze" / "members"),
    )


def _write_source_csv(tmp_path, name, content):
    source_dir = tmp_path / "source"
    source_dir.mkdir(exist_ok=True)
    (source_dir / name).write_text(content)


@pytest.fixture(autouse=True)
def _isolate_metadata_db(tmp_path, monkeypatch):
    """Redirect the engine's MetadataTracker to a per-test temp DB so tests
    never touch the real ingestion/metadata/ingestion_metadata.db."""
    test_db = str(tmp_path / "ingestion_metadata.db")
    monkeypatch.setattr(
        "ingestion.src.ingestion_engine.MetadataTracker",
        lambda db_path=test_db: MetadataTracker(db_path=test_db),
    )


def test_full_load_success(tmp_path):
    _write_source_csv(tmp_path, "members_sample.csv",
                      "member_id,first_name\nM0000001,Alex\n")
    config = _members_config(tmp_path)

    results = ingest_source("members", {"members": config})

    assert results == [("members_sample.csv", "SUCCESS")]

    out_files = list((tmp_path / "bronze" / "members").rglob("*.parquet"))
    assert len(out_files) == 1

    df = pd.read_parquet(out_files[0])
    assert list(df["member_id"]) == ["M0000001"]
    # Bronze adds only technical metadata columns, no business changes
    assert "ingestion_timestamp" in df.columns
    assert "source_file" in df.columns
    assert "file_hash" in df.columns


def test_idempotent_reprocessing_skips_second_run(tmp_path):
    _write_source_csv(tmp_path, "members_sample.csv",
                      "member_id,first_name\nM0000001,Alex\n")
    config = _members_config(tmp_path)

    first = ingest_source("members", {"members": config})
    second = ingest_source("members", {"members": config})

    assert first == [("members_sample.csv", "SUCCESS")]
    assert second == [("members_sample.csv", "SKIPPED_ALREADY_INGESTED")]

    out_files = list((tmp_path / "bronze" / "members").rglob("*.parquet"))
    assert len(out_files) == 1  # no duplicate Bronze file written


def test_force_reprocesses_already_ingested_file(tmp_path):
    _write_source_csv(tmp_path, "members_sample.csv",
                      "member_id,first_name\nM0000001,Alex\n")
    config = _members_config(tmp_path)

    ingest_source("members", {"members": config})
    second = ingest_source("members", {"members": config}, force=True)

    assert second == [("members_sample.csv", "SUCCESS")]


def test_missing_required_column_fails_and_writes_no_bronze(tmp_path):
    _write_source_csv(tmp_path, "members_sample.csv", "member_id\nM0000001\n")
    config = _members_config(tmp_path)

    results = ingest_source("members", {"members": config})

    assert results == [("members_sample.csv", "FAILED")]
    out_files = list((tmp_path / "bronze" / "members").rglob("*.parquet"))
    assert out_files == []


def test_schema_drift_warn_writes_bronze_with_drift_status(tmp_path):
    _write_source_csv(tmp_path, "members_sample.csv",
                      "member_id,first_name,extra_col\nM0000001,Alex,surprise\n")
    config = _members_config(tmp_path, schema_drift_policy="warn")

    results = ingest_source("members", {"members": config})

    assert results == [("members_sample.csv", "SUCCESS_WITH_DRIFT")]
    out_files = list((tmp_path / "bronze" / "members").rglob("*.parquet"))
    assert len(out_files) == 1


def test_schema_drift_fail_policy_fails(tmp_path):
    _write_source_csv(tmp_path, "members_sample.csv",
                      "member_id,first_name,extra_col\nM0000001,Alex,surprise\n")
    config = _members_config(tmp_path, schema_drift_policy="fail")

    results = ingest_source("members", {"members": config})

    assert results == [("members_sample.csv", "FAILED")]


def test_no_files_found_returns_empty(tmp_path):
    (tmp_path / "source").mkdir(exist_ok=True)
    config = _members_config(tmp_path)
    assert ingest_source("members", {"members": config}) == []


def test_unknown_source_raises(tmp_path):
    config = _members_config(tmp_path)
    with pytest.raises(ValueError):
        ingest_source("not_a_real_source", {"members": config})
