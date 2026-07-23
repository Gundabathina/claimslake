"""
silver_pipeline.py

CLI entry point for the Bronze -> Silver PySpark layer.

Examples:
    python -m pyspark.src.silver_pipeline --all
    python -m pyspark.src.silver_pipeline --source members
    python -m pyspark.src.silver_pipeline --source claims
    python -m pyspark.src.silver_pipeline --all --input-path bronze --output-path silver

Dependency note: claims validation needs the set of valid member,
provider, and diagnosis keys. So whenever claims is processed - even on
its own with --source claims - the three dimensions are built in memory
first to supply those keys. They are only WRITTEN to Silver when they are
part of the requested sources (or --all), so a standalone claims run does
not silently overwrite dimension outputs.
"""

import argparse
import logging
import sys
from typing import Dict, List

from pyspark.src import transformations, writers
from pyspark.src.readers import read_full_source, read_incremental_source
from pyspark.src.schemas import (
    BRONZE_DIAGNOSES_SCHEMA,
    BRONZE_MEMBERS_SCHEMA,
    BRONZE_PROVIDERS_SCHEMA,
)
from pyspark.src.spark_session import get_spark_session, stop_spark_session

logger = logging.getLogger("claimslake.silver")

ALL_SOURCES = ["members", "providers", "diagnoses", "claims"]
DIMENSIONS = ["members", "providers", "diagnoses"]

DEFAULT_INPUT = "bronze"
DEFAULT_OUTPUT = "silver"
DEFAULT_QUARANTINE = "silver/quarantine"
DEFAULT_METRICS = "data_quality/metrics"


def _log_metrics(source: str, metrics: Dict) -> None:
    logger.info("Data-quality metrics for %s:", source)
    for key, value in metrics.items():
        logger.info("    %s = %s", key, value)


def _build_dimension(spark, source: str, args):
    """Build one dimension's Silver DataFrames. Returns (valid_df,
    quarantine_df, metrics)."""
    if source == "members":
        bronze = read_full_source(spark, args.input_path, "members", BRONZE_MEMBERS_SCHEMA)
        return transformations.build_silver_members(bronze)
    if source == "providers":
        bronze = read_full_source(spark, args.input_path, "providers", BRONZE_PROVIDERS_SCHEMA)
        return transformations.build_silver_providers(bronze)
    if source == "diagnoses":
        bronze = read_full_source(spark, args.input_path, "diagnoses", BRONZE_DIAGNOSES_SCHEMA)
        return transformations.build_silver_diagnoses(bronze)
    raise ValueError("Unknown dimension: %s" % source)


def _write_source(valid, quarantine, metrics, source: str, args, partition_by=None):
    silver_path = writers.write_silver(valid, args.output_path, source, partition_by)
    quarantine_path = writers.write_quarantine(quarantine, args.quarantine_path, source)
    metrics_path = writers.write_metrics(metrics, args.metrics_path, source)
    logger.info("Silver %s written -> %s", source, silver_path)
    logger.info("Quarantine %s written -> %s", source, quarantine_path)
    logger.info("Metrics %s written -> %s", source, metrics_path)


def run(sources: List[str], args) -> int:
    spark = get_spark_session()
    exit_code = 0
    try:
        needs_claims = "claims" in sources
        # Build dimensions that are either requested or needed for claims.
        dims_to_build = [d for d in DIMENSIONS if d in sources or needs_claims]
        dim_valid = {}
        for dim in DIMENSIONS:
            if dim not in dims_to_build:
                continue
            logger.info("Building Silver dimension: %s", dim)
            valid, quarantine, metrics = _build_dimension(spark, dim, args)
            dim_valid[dim] = valid
            _log_metrics(dim, metrics)
            if dim in sources:
                _write_source(valid, quarantine, metrics, dim, args)

        if needs_claims:
            logger.info("Building Silver fact: claims")
            bronze = read_incremental_source(spark, args.input_path, "claims")
            valid, quarantine, metrics = transformations.build_silver_claims(
                bronze,
                dim_valid["members"].select("member_id").distinct(),
                dim_valid["providers"].select("provider_id").distinct(),
                dim_valid["diagnoses"].select("diagnosis_code").distinct(),
            )
            _log_metrics("claims", metrics)
            _write_source(valid, quarantine, metrics, "claims", args,
                          partition_by=["service_year_month"])
        logger.info("Silver pipeline finished successfully for: %s", ", ".join(sources))
    except Exception as exc:
        logger.exception("Silver pipeline FAILED: %s", exc)
        exit_code = 1
    finally:
        stop_spark_session(spark)
    return exit_code


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="ClaimsLake Bronze -> Silver PySpark pipeline."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", choices=ALL_SOURCES,
                       help="Process a single source.")
    group.add_argument("--all", action="store_true",
                       help="Process every source.")
    parser.add_argument("--input-path", default=DEFAULT_INPUT,
                        help="Bronze root directory (default: bronze).")
    parser.add_argument("--output-path", default=DEFAULT_OUTPUT,
                        help="Silver root directory (default: silver).")
    parser.add_argument("--quarantine-path", default=DEFAULT_QUARANTINE,
                        help="Quarantine root (default: silver/quarantine).")
    parser.add_argument("--metrics-path", default=DEFAULT_METRICS,
                        help="Metrics root (default: data_quality/metrics).")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    args = _parse_args(argv)
    sources = ALL_SOURCES if args.all else [args.source]
    return run(sources, args)


if __name__ == "__main__":
    sys.exit(main())
