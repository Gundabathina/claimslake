# Milestone 2 - Ingestion (Bronze) Interview Guide

Questions and answers about the Python ingestion layer built in Milestone 2.
Every answer reflects what the code in `ingestion/` actually does. Where
something is NOT implemented, that is stated plainly.

## 1. Explain the ingestion architecture
A config file (`ingestion/config/sources.yaml`) declares each source. The
engine (`ingestion_engine.py`) loops over the configured sources and, for
each discovered file, runs: discover + hash (`file_reader`), idempotency
check (`metadata_tracker`), read, schema validation (`schema_validator`),
Parquet write to Bronze, and an audit record. Logging and retry wrap the I/O
steps. Each concern is its own small module, so they can be tested in isolation.

## 2. Why configuration-driven ingestion?
Onboarding a new dataset should be a config change, not a code change. File
paths, columns, load type, primary key, and drift policy live in YAML, not
scattered through the engine. This keeps the engine generic and testable and
makes the full set of sources reviewable in one place.

## 3. How does idempotency work?
Each file is hashed with SHA-256. Before processing, the engine checks the
metadata DB for a prior successful ingestion of that exact (source, file_hash).
If found it skips the file - no duplicate Bronze output, no duplicate audit
row. `--force` overrides this. Re-running the pipeline is therefore safe.

## 4. How do you detect duplicate file ingestion?
By content hash, not filename. Identical bytes produce the same SHA-256, so a
resent file under a new name is still recognised as already ingested; a changed
file with the same name produces a new hash and is treated as new.

## 5. How does incremental ingestion work?
The `claims` source globs `claims_batch_*.csv`. Each batch file is
tracked independently by hash. When a new batch appears, only that new file is
ingested; previously ingested batches are skipped. It is incremental at the
FILE level.

## 6. Is this CDC? Why or why not?
No. CDC consumes an insert/update/delete change stream from a source database
transaction log. We only detect new/changed whole files by hash, and we do not
do row-level high-water-mark loading either. Calling this CDC would overstate
it.

## 7. How does metadata tracking work?
Every run inserts an `IN_PROGRESS` row in the SQLite `ingestion_log`
table, then updates it to `SUCCESS` / `SUCCESS_WITH_DRIFT` / `FAILED`
with row count, end time, target path, and any error. This gives a queryable
audit trail and drives the idempotency check.

## 8. What happens when ingestion fails?
The audit row is set to `FAILED` with the error message; no Bronze file is
written for that file; the failure is logged; and the CLI returns a non-zero
exit code. We never leave a misleading `SUCCESS` record behind.

## 9. Which errors should be retried?
Transient I/O errors (generic `OSError`, `TimeoutError`) are retried
with a short delay. Deterministic errors are not: `FileNotFoundError` (a
missing file will not reappear) and `ValueError` (bad config / failed schema
validation - retrying cannot fix the data). Retrying only helps problems that
might resolve on their own.

## 10. How is schema drift handled?
The validator flags columns beyond `expected_columns`. Behavior is
per-source via `schema_drift_policy`: `fail`, `warn`, or `allow`.
Claims use `warn` (the extra `adjustment_amount` in batch 2 is expected
evolution), so drift is logged, recorded as `SUCCESS_WITH_DRIFT`, and the
column is kept. A missing REQUIRED column always fails regardless of policy.

## 11. Why preserve raw data in Bronze?
So we can always reprocess. If a cleaning rule is later found to be wrong, we
re-derive Silver/Gold from untouched Bronze instead of having lost the original
values. Bronze is the durable system of record for what actually arrived.

## 12. Why not clean the data during ingestion?
Separation of concerns and replayability. Cleaning in ingestion bakes
assumptions into the raw layer and destroys the audit trail. We add only
technical metadata in Bronze; business rules (dedup, null handling, validity)
happen in Silver where they can be tested and changed independently.

## 13. How would this architecture change for S3?
`source_dir` and `bronze_path` become `s3://` URIs; `file_reader`
and `_write_bronze` use `boto3` / `s3fs` instead of local paths;
discovery uses `list_objects_v2` with a prefix; and the metadata store moves
from SQLite to DynamoDB or RDS so concurrent workers share state. The stage
sequence and the config-driven design stay the same.

## 14. How would this architecture change for AWS Glue?
A Glue (PySpark) job replaces the local engine for scale, reading the S3
landing prefix and writing Parquet to the Bronze prefix; a Glue Crawler / Data
Catalog registers schemas; drift surfaces as catalog schema changes;
orchestration moves to Glue triggers or Airflow. The YAML config maps to job
parameters / a Glue table definition.

## 15. How would this scale to millions of files?
Stop storing one row per file in SQLite (it becomes a bottleneck) and use a
partition/manifest approach with a scalable metadata store; parallelize with
Spark/Glue; discover via S3 inventory instead of listing; and batch small files
into larger Parquet files to avoid the small-files problem.

## 16. How would you handle late-arriving data?
The synthetic data intentionally includes late claims (large gap between
`service_date` and `submission_date`). Ingestion loads them normally;
the reprocessing/backfill strategy (re-run the affected `ingestion_date`
partition and recompute downstream) is a Silver/Gold concern. Bronze partitions
by ingestion date, so late data lands in the partition of the day it arrived.

## 17. Exactly-once vs at-least-once?
The pipeline is at-least-once at the trigger level (a run can be retried) but
made effectively exactly-once for Bronze output through idempotency: the hash
check plus a deterministic output path mean reprocessing the same file does not
create duplicates.

## 18. How would you monitor this in production?
Query `ingestion_log` for failures, drift events, row-count anomalies, and
runtime; emit those as metrics (CloudWatch/Prometheus); and in Airflow
(Milestone 6) rely on task success/failure, SLAs, and retries.

## 19. How would you implement alerting?
Trigger on `FAILED` rows, on `SUCCESS_WITH_DRIFT` (so schema changes get
a human look), and on row counts outside expected bounds - routed to
email/Slack/PagerDuty, or via Airflow failure callbacks and CloudWatch alarms
once deployed.

## 20. How would you handle corrupted files?
A malformed CSV surfaces as a read/parse error or a schema failure; the file is
recorded `FAILED` and skipped, not written to Bronze. A production hardening
step would quarantine the bad file to a separate prefix for inspection while
letting healthy files proceed.

## Honest limitations of this milestone
- Local only: no S3/Glue/DynamoDB is actually used yet; those answers describe
  the intended cloud design, not something deployed.
- File-level incremental only: no row-level high-water mark and no CDC.
- Quarantine and alerting are described, not implemented.
- Record counts in examples are illustrative; run it locally for real numbers.
