"""
Tests for ingestion/src/metadata_tracker.py

Each test uses a fresh SQLite file inside a pytest tmp_path, so tests are
isolated and never touch the real ingestion/metadata database.
"""

import os

from ingestion.src.metadata_tracker import MetadataTracker


def _tracker(tmp_path):
    return MetadataTracker(db_path=os.path.join(str(tmp_path), "test_metadata.db"))


def test_start_creates_in_progress_record(tmp_path):
    tracker = _tracker(tmp_path)
    ingestion_id = tracker.start("members", "members_sample.csv", "abc123", "full")

    history = tracker.history("members")
    assert len(history) == 1
    assert history[0]["ingestion_id"] == ingestion_id
    assert history[0]["status"] == "IN_PROGRESS"


def test_complete_updates_status_and_count(tmp_path):
    tracker = _tracker(tmp_path)
    ingestion_id = tracker.start("members", "members_sample.csv", "abc123", "full")
    tracker.complete(ingestion_id, record_count=100, status="SUCCESS",
                     target_path="bronze/members/x.parquet")

    row = tracker.history("members")[0]
    assert row["status"] == "SUCCESS"
    assert row["record_count"] == 100
    assert row["target_path"] == "bronze/members/x.parquet"


def test_fail_records_error_message(tmp_path):
    tracker = _tracker(tmp_path)
    ingestion_id = tracker.start("members", "members_sample.csv", "abc123", "full")
    tracker.fail(ingestion_id, "Missing required column: first_name")

    row = tracker.history("members")[0]
    assert row["status"] == "FAILED"
    assert "first_name" in row["error_message"]


def test_already_ingested_false_before_success(tmp_path):
    tracker = _tracker(tmp_path)
    assert tracker.already_ingested("members", "abc123") is False


def test_already_ingested_true_after_success(tmp_path):
    tracker = _tracker(tmp_path)
    ingestion_id = tracker.start("members", "members_sample.csv", "abc123", "full")
    tracker.complete(ingestion_id, 10, "SUCCESS", "bronze/members/x.parquet")
    assert tracker.already_ingested("members", "abc123") is True


def test_already_ingested_true_after_success_with_drift(tmp_path):
    tracker = _tracker(tmp_path)
    ingestion_id = tracker.start("claims", "claims_batch_2.csv", "def456", "incremental")
    tracker.complete(ingestion_id, 10, "SUCCESS_WITH_DRIFT", "bronze/claims/x.parquet")
    assert tracker.already_ingested("claims", "def456") is True


def test_already_ingested_false_after_failure(tmp_path):
    tracker = _tracker(tmp_path)
    ingestion_id = tracker.start("members", "members_sample.csv", "abc123", "full")
    tracker.fail(ingestion_id, "boom")
    assert tracker.already_ingested("members", "abc123") is False
