# ingestion/

Configuration-driven Python framework that reads the synthetic source CSV
files from Milestone 1 (`data/sample/`) and loads them into the local
Bronze layer (`bronze/`) with full auditability, retry handling, and
schema-drift detection.

Adding a new source dataset means adding an entry to
`ingestion/config/sources.yaml` - not writing new ingestion code.

**Note:** All data is synthetic. See the root README and
`docs/data_dictionary/` for the source schemas.

## Architecture

~~~
data/sample/*.csv
        |
        v
config_loader.py   <--  ingestion/config/sources.yaml
        |
        v
file_reader.py     (discover files, SHA-256 hash, read CSV)
        |
        v
metadata_tracker   -- already ingested this file_hash? --> SKIP (idempotent)
        |  no
        v
schema_validator   (required columns + drift policy)
        |  FAILED --> record failure, stop this file
        v  PASSED / PASSED_WITH_DRIFT
_write_bronze()    --> bronze/<source>/ingestion_date=YYYY-MM-DD/<file>.parquet
        |
        v
metadata_tracker   (record SUCCESS / SUCCESS_WITH_DRIFT, row count, path)
~~~

Each stage is a separate, independently testable module under `ingestion/src/`:

| Module | Responsibility |
| --- | --- |
| `config_loader.py` | Load + validate `config/sources.yaml` into typed `SourceConfig` objects |
| `file_reader.py` | Discover files, compute SHA-256 hashes, read CSV rows |
| `schema_validator.py` | Compare actual vs configured columns; detect drift |
| `metadata_tracker.py` | SQLite audit log; powers the idempotency check |
| `retry_handler.py` | Retry transient failures; fail fast on non-recoverable ones |
| `logger.py` | Console + file logging |
| `ingestion_engine.py` | Orchestrates the above; exposes the CLI |

## Configuration-driven ingestion

Every source is declared in `ingestion/config/sources.yaml`. Each entry
specifies the source directory and file glob, the load type, the expected and
required columns, the primary key, the schema-drift policy, and the Bronze
output path. The engine reads this config and processes sources dynamically,
so onboarding a new dataset is a config change, not a code change.

## Full vs incremental load

**Full load** (`members`, `providers`, `diagnoses`): reference /
dimension sources whose whole contents are re-read each run.

**Incremental load** (`claims`): the claims source matches multiple files
(`claims_batch_1*.csv`, `claims_batch_2*.csv`). New files are ingested;
files already ingested successfully are skipped. This is incremental FILE
ingestion - not row-level incremental and not CDC (see below).

### Incremental file ingestion vs record-level vs CDC

- Incremental file ingestion (what we do): the unit of work is a whole file,
  identified by name + SHA-256 content hash. A new or changed file is
  processed; an unchanged, already-ingested file is skipped.
- Incremental record ingestion (not implemented): would track a high-water
  mark (e.g. max `submission_date` or an autoincrement id) and pull only
  rows newer than the last run.
- Change data capture / CDC (not implemented): would consume an
  insert/update/delete change stream from the source database log. We do not
  read a change log, so we do not call this CDC.

## Idempotency

Before processing a file the engine computes its SHA-256 hash and asks the
metadata store whether that exact (source, file_hash) has already been
ingested successfully. If so, the file is skipped and no duplicate Bronze file
or metadata row is written. `--force` bypasses the check to deliberately
reprocess.

This matters in production because pipelines are re-run constantly (retries,
backfills, restarts). An idempotent pipeline can be safely re-run without
double-writing data or corrupting downstream counts.

Idempotency here is a file-level operational guard. It is NOT business-record
deduplication - duplicate claim rows within a file are intentionally preserved
in Bronze and removed later in Silver (Milestone 3).

## Metadata tracking

Every run writes an audit row to a SQLite database at
`ingestion/metadata/ingestion_metadata.db` (table `ingestion_log`),
capturing: `ingestion_id`, `source_name`, `source_file`,
`file_hash`, `ingestion_start_time`, `ingestion_end_time`,
`record_count`, `status`, `error_message`, `load_type`, and
`target_path`.

SQLite was chosen over a flat CSV/JSON log because the idempotency check needs
a real indexed lookup, and over a full database server because that would be
unnecessary operational overhead for a local project.

## Retry logic

Transient failures (generic `OSError`, `TimeoutError`) are retried up to
3 times with a fixed 2-second delay, and each attempt is logged.
Non-recoverable failures are NOT retried: `FileNotFoundError` (the file will
not appear on a retry) and `ValueError` (bad config or failed schema
validation - retrying cannot fix bad data). This distinction avoids wasting
time re-running failures that can never succeed.

## Schema drift

The schema validator compares a file's columns against the source's
`required_columns` and `expected_columns`:

- A missing required column is always a hard failure - the file is
  structurally broken.
- An unexpected column (present in the file, not in `expected_columns`) is
  schema drift, handled per the source `schema_drift_policy`: `fail`,
  `warn`, or `allow`.

`claims_batch_2` intentionally adds an `adjustment_amount` column that
`claims_batch_1` does not have. The `claims` source uses
`schema_drift_policy: warn`, so this real, additive schema evolution is
logged, recorded in metadata (status `SUCCESS_WITH_DRIFT`), and carried
through to Bronze rather than silently dropped or hard-failed. Reference
sources (`members`, `providers`, `diagnoses`) use `fail` because
an unexpected column there signals an upstream problem worth stopping for.

## Bronze-layer design principle

Bronze preserves the source as faithfully as possible. The engine adds only
technical metadata columns (`ingestion_timestamp`, `source_file`,
`file_hash`) and performs NO business transformation - no deduplication, no
fixing negative paid amounts, no correcting invalid diagnosis or state codes,
no date repair. Those belong to Silver (Milestone 3) and Gold (Milestone 4).
Keeping Bronze raw means we can always replay history and never lose
information a later rule might need.

## Data format

Bronze is written as Parquet, partitioned by ingestion date
(`ingestion_date=YYYY-MM-DD`). Parquet is columnar, compressed, and
schema-aware, which fits a lake / medallion design and the later PySpark stage.
Tradeoff: Parquet needs `pandas` + `pyarrow` (declared in
`requirements.txt`), whereas CSV/JSON would be dependency-free but larger
and slower to scan. Since the project already commits to a Parquet-based lake,
the dependency is justified.

## CLI

~~~
# one source, using its configured load type
python -m ingestion.src.ingestion_engine --source members --mode full
python -m ingestion.src.ingestion_engine --source claims --mode incremental

# every configured source
python -m ingestion.src.ingestion_engine --all

# force reprocessing (bypass the idempotency skip)
python -m ingestion.src.ingestion_engine --all --force
~~~

`--mode` documents intent; the authoritative load type is whatever
`sources.yaml` declares for that source (a mismatch is logged as a warning).

## Testing

~~~
pip install -r requirements.txt
pytest tests/ingestion -v
~~~

Tests live in `tests/ingestion/` and exercise the real logic against
temporary files and a temporary SQLite DB: full load, missing file / missing
column, schema drift (`warn` and `fail`), idempotent reprocessing,
`--force`, metadata tracking, and unknown-source handling.

## Example log output (format illustration)

~~~
INFO     claimslake.ingestion - Starting ingestion
INFO     claimslake.ingestion - Source: claims_batch_1_sample.csv
INFO     claimslake.ingestion - Load type: incremental
INFO     claimslake.ingestion - Records read: 60
INFO     claimslake.ingestion - Schema validation: PASSED - Schema matches expected columns exactly.
INFO     claimslake.ingestion - Bronze write: SUCCESS -> bronze/claims/ingestion_date=2026-07-22/claims_batch_1_sample.parquet
INFO     claimslake.ingestion - Metadata recorded
INFO     claimslake.ingestion - Ingestion completed
~~~

Record counts depend on the data you generate locally; the lines above
illustrate the log FORMAT and are not measured figures.

## Status

Milestone 2 code is complete and statically reviewed. The automated tests must
be executed locally (`pytest tests/ingestion`) to confirm they pass in your
environment. See the root README and the interview guide for an honest account
of what was executed versus what still needs local verification.
