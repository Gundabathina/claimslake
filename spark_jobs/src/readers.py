"""
readers.py

Reads Bronze Parquet output into Spark DataFrames.

Two strategies are used, matching how ingestion/config/sources.yaml
defines each source's load_type:

- FULL load sources (members, providers, diagnoses): every ingestion run
  rewrites the whole table into a new ingestion_date=YYYY-MM-DD
  partition. Reading every historical partition would reprocess the same
  logical data repeatedly (and massively inflate duplicate counts), so
  read_full_source reads only the MOST RECENT ingestion_date partition.

- INCREMENTAL load source (claims): each file is a genuinely new batch,
  so read_incremental_source reads every ingestion_date partition, with
  mergeSchema enabled so claims_batch_1.csv (no adjustment_amount) and
  claims_batch_2.csv (has adjustment_amount) can be read together
  without either file being skipped or the read failing on the mismatch.

Partition discovery is done driver-side with the standard library
(glob/os) because this runs locally against a filesystem path. On S3 the
same idea would use a catalog (Glue) or a listing API instead.
"""

import glob
import os
from typing import List, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StructType

PARTITION_PREFIX = "ingestion_date="


def _list_ingestion_date_partitions(source_bronze_dir: str) -> List[str]:
    pattern = os.path.join(source_bronze_dir, PARTITION_PREFIX + "*")
    return sorted(d for d in glob.glob(pattern) if os.path.isdir(d))


def _partition_date(partition_dir: str) -> str:
    return os.path.basename(partition_dir).split("=", 1)[1]


def read_full_source(
    spark: SparkSession,
    bronze_root: str,
    source_name: str,
    schema: Optional[StructType] = None,
) -> DataFrame:
    """Read only the latest ingestion_date partition of a full-load
    source, applying an explicit all-string schema (see schemas.py)."""
    source_dir = os.path.join(bronze_root, source_name)
    partitions = _list_ingestion_date_partitions(source_dir)
    if not partitions:
        raise FileNotFoundError(
            "No Bronze partitions found for source '%s' under %s. "
            "Run the ingestion layer first: "
            "python -m ingestion.src.ingestion_engine --all" % (source_name, source_dir)
        )
    latest = partitions[-1]
    reader = spark.read
    if schema is not None:
        reader = reader.schema(schema)
    df = reader.parquet(latest)
    # Preserve which Bronze partition this row came from, for lineage.
    return df.withColumn(
        "bronze_ingestion_date", df["ingestion_timestamp"].substr(1, 10)
    )


def read_incremental_source(
    spark: SparkSession,
    bronze_root: str,
    source_name: str,
) -> DataFrame:
    """Read ALL ingestion_date partitions of an incremental source with
    mergeSchema, so evolving batch schemas are unioned into one
    DataFrame. Explicit schema is intentionally NOT forced here so the
    additive adjustment_amount column from batch_2 is picked up; the
    columns are still all string in Bronze, and cleaners.clean_claims
    performs the explicit casting afterwards."""
    source_dir = os.path.join(bronze_root, source_name)
    partitions = _list_ingestion_date_partitions(source_dir)
    if not partitions:
        raise FileNotFoundError(
            "No Bronze partitions found for source '%s' under %s. "
            "Run the ingestion layer first: "
            "python -m ingestion.src.ingestion_engine --all" % (source_name, source_dir)
        )
    df = (
        spark.read.option("mergeSchema", "true")
        .option("basePath", source_dir)
        .parquet(*partitions)
    )
    return df
