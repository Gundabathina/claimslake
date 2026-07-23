"""
writers.py

Persists Silver output: cleaned datasets, quarantined records, and
data-quality metrics.

- Silver and quarantine data are written as Parquet (columnar, typed,
  splittable, and read efficiently by the downstream Gold layer).
- Metrics are a small driver-side dictionary, so they are written as
  plain JSON with the standard library rather than as a Spark job - one
  tiny JSON file is far more useful here than a distributed write.

Write mode is "overwrite" so the Silver layer is fully reproducible: a
re-run reproduces the same Silver state from Bronze rather than appending
duplicates. This is the Silver-layer analogue of the Bronze idempotency
guarantee.
"""

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

from pyspark.sql import DataFrame


def write_silver(
    df: DataFrame,
    output_root: str,
    dataset: str,
    partition_by: Optional[List[str]] = None,
) -> str:
    """Write a cleaned Silver dataset to output_root/dataset as Parquet.
    Partitions only when partition_by is given (callers pass a partition
    column only where it earns its keep - see transformations.py)."""
    path = os.path.join(output_root, dataset)
    writer = df.write.mode("overwrite")
    if partition_by:
        writer = writer.partitionBy(*partition_by)
    writer.parquet(path)
    return path


def write_quarantine(df: DataFrame, quarantine_root: str, dataset: str) -> str:
    """Write rejected records to quarantine_root/dataset as Parquet.
    Not partitioned: rejected volume is small and partitioning it would
    just create many tiny files. Each record already carries
    rejection_reason and validation_timestamp (added in
    validators.split_valid_quarantine)."""
    path = os.path.join(quarantine_root, dataset)
    df.write.mode("overwrite").parquet(path)
    return path


def write_metrics(metrics: dict, metrics_root: str, dataset: str) -> str:
    """Write a data-quality metrics dict to JSON. Two files are written:
    a timestamped historical record and a stable 'latest' file for easy
    inspection. Metrics are only ever populated from real pipeline
    execution (see transformations.py); this function never invents
    numbers."""
    os.makedirs(metrics_root, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    enriched = dict(metrics)
    enriched["dataset"] = dataset
    enriched["generated_at"] = datetime.now(timezone.utc).isoformat()
    history_path = os.path.join(metrics_root, "%s_%s.json" % (dataset, ts))
    latest_path = os.path.join(metrics_root, "%s_latest.json" % dataset)
    for p in (history_path, latest_path):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(enriched, f, indent=2, sort_keys=True)
    return latest_path
