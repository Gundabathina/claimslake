"""
test_deduplication.py

Tests for spark_jobs/src/deduplication.py: exact-duplicate-row collapsing,
deterministic business-key survivor selection, and the history-counting
helper used to keep provider versions.
"""

from pyspark.sql import Row

from spark_jobs.src import deduplication


def test_drop_exact_duplicate_rows(spark):
    df = spark.createDataFrame([
        Row(id="1", v="a"),
        Row(id="1", v="a"),   # exact duplicate
        Row(id="2", v="b"),
    ])
    deduped, dup_count = deduplication.drop_exact_duplicate_rows(df, ["id", "v"])
    assert deduped.count() == 2
    assert dup_count == 1


def test_deduplicate_by_key_picks_latest_deterministically(spark):
    df = spark.createDataFrame([
        Row(k="M1", ts="2024-01-01T00:00:00+00:00", payload="old"),
        Row(k="M1", ts="2024-05-01T00:00:00+00:00", payload="new"),
        Row(k="M2", ts="2024-02-01T00:00:00+00:00", payload="solo"),
    ])
    survivors, dup_count = deduplication.deduplicate_by_key(
        df,
        business_keys=["k"],
        order_by_desc_columns=["ts"],
        tiebreak_hash_columns=["k", "ts", "payload"],
    )
    result = {r["k"]: r["payload"] for r in survivors.collect()}
    assert survivors.count() == 2
    assert dup_count == 1
    assert result["M1"] == "new"     # latest ts survives
    assert result["M2"] == "solo"


def test_deduplicate_by_key_is_deterministic_on_ties(spark):
    # Identical ordering columns: the content hash tiebreak must make the
    # survivor stable across repeated runs.
    rows = [
        Row(k="X", ts="2024-01-01T00:00:00+00:00", payload="alpha"),
        Row(k="X", ts="2024-01-01T00:00:00+00:00", payload="beta"),
    ]
    df = spark.createDataFrame(rows)
    first = deduplication.deduplicate_by_key(
        df, ["k"], ["ts"], ["k", "ts", "payload"]
    )[0].collect()[0]["payload"]
    second = deduplication.deduplicate_by_key(
        df, ["k"], ["ts"], ["k", "ts", "payload"]
    )[0].collect()[0]["payload"]
    assert first == second


def test_count_key_groups_with_history(spark):
    df = spark.createDataFrame([
        Row(provider_id="P1", v="in"),
        Row(provider_id="P1", v="out"),   # P1 has 2 versions -> history
        Row(provider_id="P2", v="in"),
    ])
    assert deduplication.count_key_groups_with_history(df, ["provider_id"]) == 1
