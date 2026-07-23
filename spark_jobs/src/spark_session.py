"""
spark_session.py

Creates the single SparkSession used by every Silver transformation job.

Local-mode configuration choices (see spark_jobs/README.md for the full
explanation):
  - master("local[*]") - runs Spark on the local machine using all
    available cores. There is no cluster in this project; PySpark still
    gives us the real DataFrame API, explicit schemas, and
    distributed-style operations (joins, window functions, shuffles)
    even though everything executes on one machine.
  - spark.sql.shuffle.partitions is lowered from Spark's default of 200
    to a small number. 200 is tuned for large multi-node clusters; on a
    local run against a few thousand synthetic rows, 200 shuffle
    partitions creates hundreds of tiny tasks and output files with far
    more scheduling overhead than actual work. A small number keeps
    partitions a sensible size for this data volume. On a real cluster
    with far more data, this would be set based on data volume and
    cluster size, not left at a fixed constant.
  - spark.sql.session.timeZone is pinned to UTC so date and timestamp
    handling is deterministic regardless of the machine running the job
    - important because Bronze ingestion timestamps are stored as UTC
    ISO-8601 strings.
"""

import os

from pyspark.sql import SparkSession

DEFAULT_SHUFFLE_PARTITIONS = "8"


def get_spark_session(app_name: str = "claimslake-silver") -> SparkSession:
    """Return a configured local SparkSession. Safe to call multiple
    times - getOrCreate() reuses an existing session in the same
    process, which is what the test suite relies on."""
    spark = (
        SparkSession.builder.appName(app_name)
        .master(os.environ.get("SPARK_MASTER", "local[*]"))
        .config(
            "spark.sql.shuffle.partitions",
            os.environ.get("SPARK_SHUFFLE_PARTITIONS", DEFAULT_SHUFFLE_PARTITIONS),
        )
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def stop_spark_session(spark: SparkSession) -> None:
    """Stop the given SparkSession. Split out as its own function so the
    CLI entry point manages session lifecycle explicitly and tests can
    choose not to stop a shared session between cases."""
    spark.stop()
