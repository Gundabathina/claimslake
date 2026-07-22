"""
ingestion_engine.py

Main orchestration for the ClaimsLake Bronze ingestion layer.

For each configured source, and each file discovered for that source:
  1. Discover the file(s) and compute a content hash    (file_reader)
  2. Idempotency check: already ingested this exact file? (metadata_tracker)
  3. Read the file                                       (file_reader, via retry)
  4. Validate schema: required columns + drift           (schema_validator)
  5. Write raw rows to Bronze as Parquet, partitioned     (_write_bronze, via retry)
     by ingestion date, adding ONLY technical metadata
  6. Record ingestion metadata                           (metadata_tracker)
  7. Log every step                                      (logger)

Run as a module:
    python -m ingestion.src.ingestion_engine --source members --mode full
    python -m ingestion.src.ingestion_engine --source claims --mode incremental
    python -m ingestion.src.ingestion_engine --all
    python -m ingestion.src.ingestion_engine --all --force
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import pandas as pd

from ingestion.src.config_loader import SourceConfig, load_sources
from ingestion.src.file_reader import DiscoveredFile, discover_files, read_csv
from ingestion.src.logger import get_logger
from ingestion.src.metadata_tracker import MetadataTracker
from ingestion.src.retry_handler import IngestionError, run_with_retry
from ingestion.src.schema_validator import validate_schema

logger = get_logger(__name__)


def _write_bronze(config: SourceConfig, discovered: DiscoveredFile,
                  header: List[str], rows: List[dict], ingestion_ts: str) -> str:
    """Write raw rows to the Bronze layer as Parquet, partitioned by
    ingestion date. Adds ONLY technical metadata columns
    (ingestion_timestamp, source_file, file_hash) - no business
    transformation happens here (see Bronze-layer design principle in
    ingestion/README.md)."""
    df = pd.DataFrame(rows, columns=header)
    df["ingestion_timestamp"] = ingestion_ts
    df["source_file"] = discovered.file_name
    df["file_hash"] = discovered.file_hash

    partition_date = ingestion_ts[:10]  # YYYY-MM-DD
    out_dir = os.path.join(config.bronze_path_abs,
                           "ingestion_date=%s" % partition_date)
    os.makedirs(out_dir, exist_ok=True)

    file_stem = os.path.splitext(discovered.file_name)[0]
    out_path = os.path.join(out_dir, "%s.parquet" % file_stem)
    df.to_parquet(out_path, index=False)
    return out_path


def _process_file(config: SourceConfig, discovered: DiscoveredFile,
                  tracker: MetadataTracker, force: bool) -> str:
    """Process a single discovered file end to end. Returns a status string."""
    logger.info("Starting ingestion")
    logger.info("Source: %s", discovered.file_name)
    logger.info("Load type: %s", config.load_type)

    if not force and tracker.already_ingested(config.name, discovered.file_hash):
        logger.info(
            "Skipping %s - identical content already ingested successfully "
            "(idempotency check via file_hash). Use --force to reprocess.",
            discovered.file_name,
        )
        return "SKIPPED_ALREADY_INGESTED"

    ingestion_ts = datetime.now(timezone.utc).isoformat()
    ingestion_id = tracker.start(
        config.name, discovered.file_name, discovered.file_hash, config.load_type
    )

    try:
        header, rows = run_with_retry(
            read_csv, discovered.path,
            max_retries=3, delay_seconds=2.0, source_name=config.name,
        )
        record_count = len(rows)
        logger.info("Records read: %d", record_count)

        result = validate_schema(header, config)
        logger.info("Schema validation: %s - %s", result.status, result.message)

        if not result.passed:
            tracker.fail(ingestion_id, result.message)
            logger.error("Ingestion FAILED for %s: %s",
                         discovered.file_name, result.message)
            return "FAILED"

        if result.status == "PASSED_WITH_DRIFT":
            logger.warning("Schema drift recorded for %s: %s",
                           discovered.file_name, result.unexpected_columns)

        out_path = run_with_retry(
            _write_bronze, config, discovered, header, rows, ingestion_ts,
            max_retries=3, delay_seconds=2.0, source_name=config.name,
        )
        logger.info("Bronze write: SUCCESS -> %s", out_path)

        final_status = "SUCCESS" if result.status == "PASSED" else "SUCCESS_WITH_DRIFT"
        tracker.complete(ingestion_id, record_count, final_status, out_path)
        logger.info("Metadata recorded")
        logger.info("Ingestion completed")
        return final_status

    except IngestionError as exc:
        tracker.fail(ingestion_id, str(exc))
        logger.error("Ingestion FAILED for %s: %s", discovered.file_name, exc)
        return "FAILED"
    except Exception as exc:  # record any unexpected failure honestly
        tracker.fail(ingestion_id, "Unexpected error: %s" % exc)
        logger.exception("Unexpected error ingesting %s", discovered.file_name)
        return "FAILED"


def ingest_source(source_name: str, sources: Dict[str, SourceConfig],
                  force: bool = False) -> List[Tuple[str, str]]:
    """Ingest every discovered file for one configured source.
    Returns a list of (file_name, status) tuples."""
    if source_name not in sources:
        raise ValueError(
            "Unknown source '%s'. Configured sources: %s"
            % (source_name, list(sources.keys()))
        )

    config = sources[source_name]
    tracker = MetadataTracker()
    discovered_files = discover_files(config)

    if not discovered_files:
        logger.warning(
            "No files found for source '%s' matching pattern '%s' in %s",
            source_name, config.file_pattern, config.source_dir,
        )
        return []

    results: List[Tuple[str, str]] = []
    for discovered in discovered_files:
        status = _process_file(config, discovered, tracker, force)
        results.append((discovered.file_name, status))
    return results


def run_all(sources: Dict[str, SourceConfig],
            force: bool = False) -> Dict[str, List[Tuple[str, str]]]:
    return {name: ingest_source(name, sources, force=force) for name in sources}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ClaimsLake Bronze ingestion engine - reads configured "
                    "source CSV files and loads them into the Bronze layer."
    )
    parser.add_argument(
        "--source",
        help="Name of a single configured source to ingest "
             "(members, providers, diagnoses, claims)",
    )
    parser.add_argument(
        "--all", action="store_true", help="Ingest every configured source"
    )
    parser.add_argument(
        "--mode", choices=["full", "incremental"],
        help="Documents/overrides the intended load mode for this run. Per-file "
             "idempotency and drift behavior are always driven by "
             "ingestion/config/sources.yaml regardless of this flag.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Reprocess files even if already ingested (bypasses the "
             "idempotency check).",
    )
    return parser


def main(argv=None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if not args.source and not args.all:
        parser.error("Specify --source <name> or --all")

    sources = load_sources()

    if (args.mode and args.source and args.source in sources
            and args.mode != sources[args.source].load_type):
        logger.warning(
            "--mode %s was requested but source '%s' is configured as '%s' in "
            "sources.yaml; the configured load_type remains the source of truth.",
            args.mode, args.source, sources[args.source].load_type,
        )

    any_failed = False
    if args.all:
        for _source, results in run_all(sources, force=args.force).items():
            any_failed = any_failed or any(s == "FAILED" for _f, s in results)
    else:
        results = ingest_source(args.source, sources, force=args.force)
        any_failed = any(s == "FAILED" for _f, s in results)

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
