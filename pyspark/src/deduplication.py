"""
deduplication.py

Deterministic deduplication for the Silver layer.

Two distinct kinds of "duplicate" are handled separately because they
mean different things:

1. Exact duplicate rows - the same record appears more than once with
   identical values in every business column (e.g. a resent enrollment
   file, or a resubmitted claim). These are pure redundancy and are
   always safe to collapse to one row. drop_exact_duplicate_rows()
   handles this.

2. Multiple rows sharing the same business key but with DIFFERENT
   values (e.g. a provider whose network_status changed between two feed
   dates). These are NOT redundant - they carry real information - so
   collapsing them naively would destroy history. deduplicate_by_key()
   picks a single deterministic survivor per key, but callers decide
   whether that collapsing is even appropriate for a given dataset.
   providers deliberately does NOT collapse its historical versions
   (see transformations.build_silver_providers) so the change history
   survives for the future Gold-layer SCD Type 2 dimension.
"""

from typing import List, Tuple

from pyspark.sql import Column, DataFrame, functions as F
from pyspark.sql.window import Window


def drop_exact_duplicate_rows(
    df: DataFrame, business_columns: List[str]
) -> Tuple[DataFrame, int]:
    """Collapse rows that are identical across business_columns.

    business_columns intentionally EXCLUDES the Bronze technical metadata
    columns (ingestion_timestamp, source_file, file_hash): two ingestions
    of the same resent file carry different metadata even though the
    business data is byte-identical, and it is the business data we are
    de-duplicating on. Returns (deduped_df, exact_duplicate_count)."""
    before = df.count()
    deduped = df.dropDuplicates(business_columns)
    after = deduped.count()
    return deduped, before - after


def deduplicate_by_key(
    df: DataFrame,
    business_keys: List[str],
    order_by_desc_columns: List[str],
    tiebreak_hash_columns: List[str],
) -> Tuple[DataFrame, int]:
    """Keep exactly one deterministic survivor per business_keys group.

    Survivor selection is fully deterministic:
      1. Within each key group, order candidates by order_by_desc_columns
         (all descending, so most-recent / most-complete wins - callers
         choose e.g. ingestion_timestamp).
      2. Break any remaining tie with a SHA-256 hash over
         tiebreak_hash_columns, also descending. Because the hash is a
         pure function of the row's own content, the choice is
         reproducible across runs (not random). "Deterministic" here
         means the same input always yields the same survivor - it does
         NOT mean every re-run re-picks a "better" row.

    Returns (survivors_df, duplicate_row_count), where
    duplicate_row_count is the number of NON-survivor rows removed."""
    before = df.count()
    tiebreak = F.sha2(
        F.concat_ws(
            "|",
            *[F.coalesce(F.col(c).cast("string"), F.lit("")) for c in tiebreak_hash_columns]
        ),
        256,
    )
    ranked = df.withColumn("_tiebreak_hash", tiebreak)
    order_cols = [F.col(c).desc_nulls_last() for c in order_by_desc_columns]
    order_cols.append(F.col("_tiebreak_hash").desc())
    window = Window.partitionBy(*business_keys).orderBy(*order_cols)
    ranked = ranked.withColumn("_row_number", F.row_number().over(window))
    survivors = ranked.filter(F.col("_row_number") == 1).drop(
        "_row_number", "_tiebreak_hash"
    )
    after = survivors.count()
    return survivors, before - after


def count_key_groups_with_history(
    df: DataFrame, business_keys: List[str]
) -> int:
    """Count business keys that appear on more than one row. For
    providers this is the number of providers that carry a change
    history (multiple network_status/effective_date versions) - a
    metric we surface rather than a set of rows we delete."""
    grouped = df.groupBy(*business_keys).agg(F.count(F.lit(1)).alias("_n"))
    return grouped.filter(F.col("_n") > 1).count()
