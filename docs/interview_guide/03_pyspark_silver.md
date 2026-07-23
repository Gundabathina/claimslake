# Interview Guide - Milestone 3: PySpark Silver Layer

Every answer below is grounded in what this project actually implements
(see `pyspark/src/`). All data is synthetic. Where a technique is only
described (not implemented at scale), that is stated plainly.

## 1. Why PySpark for the Silver layer?
Silver is where distributed-style transformations belong: joins for
referential integrity, window functions for deduplication, and typed
columnar writes. PySpark gives the real DataFrame API and execution model
a production platform would use, so the same code scales from a laptop to
a cluster. Here it runs `local[*]` on synthetic data, but the code is
cluster-shaped.

## 2. Why not just pandas?
pandas is single-node and in-memory. The whole point of Silver is to
demonstrate scalable patterns (shuffles, broadcast joins, partitioned
writes, window functions). pandas is still used - but only in the Bronze
ingestion layer to write small Parquet files, which is honest about where
each tool fits.

## 3. Why Bronze/Silver separation at all?
Bronze preserves the raw source faithfully so any downstream bug can be
traced and reprocessed without re-pulling the source. Silver applies
business rules (cleaning, dedup, validation). Keeping them separate means
a change to business logic never risks the raw record of truth.

## 4. Why Parquet for Silver output?
Parquet is columnar, typed, compressed, and splittable, so downstream Gold
queries read only the columns they need with predicate/partition pushdown.
It also carries a real schema, unlike the all-string CSV/Parquet Bronze.

## 5. How does deduplication work here?
Two stages (`deduplication.py`). First `drop_exact_duplicate_rows`
collapses byte-identical business rows (resent files). Then
`deduplicate_by_key` uses a window partitioned by the business key,
ordered descending by recency, keeping `row_number() == 1`.

## 6. What is the business key for each dataset?
members: `member_id`. diagnoses: `diagnosis_code`. claims:
`claim_id` (one surviving row per claim). providers: the version grain
is `(provider_id, effective_date)` - NOT `provider_id` alone,
because providers keep history (see Q8).

## 7. How is the dedup survivor chosen, and is it deterministic?
Yes. The window orders by recency columns descending (e.g.
`ingestion_timestamp`), then by a SHA-256 hash of the row's own content
as a final tiebreak. Because the tiebreak is a pure function of the row, the
same input always yields the same survivor - deterministic and reproducible,
not random. Note: ISO-8601 UTC timestamps sort correctly as strings, so no
timestamp parse is needed for ordering.

## 8. How do you handle duplicate providers vs real provider changes?
This is the key provider rule. Byte-identical provider rows are true
duplicates and are collapsed. But rows that share `provider_id` and
differ in `network_status`/`effective_date` are legitimate
historical versions and are PRESERVED as distinct rows. Silver does not
collapse them because destroying that history would make the future Gold
SCD Type 2 dimension impossible. The number of providers carrying history
is reported in metrics (`providers_with_historical_versions_preserved`).

## 9. How does Silver prepare providers for SCD Type 2?
By preserving every distinct `(provider_id, effective_date)` version and
keeping `network_status` and `effective_date` intact. Gold can then
order versions per provider and derive `valid_from`/`valid_to`/
`is_current`. Silver deliberately does NOT compute those columns yet -
that is Gold's job.

## 10. How do you handle nulls?
CSV blanks are first converted to true nulls (`blank_to_null`) so casts
and `isNull()` checks behave correctly. Then nulls are treated per
business rule: some are quarantine reasons (e.g. missing required key),
some are expected and only flagged (missing zip, missing specialty), and
some are valid (a Pending claim with no `paid_amount`).

## 11. How do you handle invalid data?
Field-level rules in `validators.py` (invalid state code, future date of
birth, negative paid amount, a Paid claim missing its amount, invalid
status, submission before service). Failing rows are quarantined with a
`rejection_reason`; they are never silently dropped or "corrected".

## 12. What is quarantine and why use it?
Quarantine is a parallel output (`silver/quarantine/<dataset>/`) holding
rejected records with `rejection_reason` and `validation_timestamp`.
It keeps Silver clean without losing evidence: bad records stay auditable
and can be investigated or reprocessed, instead of vanishing.

## 13. How do you handle referential integrity?
Claims foreign keys (member, provider, diagnosis) are checked with left
joins against the valid Silver dimension key sets; any key that does not
resolve produces a quarantine reason (e.g.
`invalid_diagnosis_code_reference`). Orphans are quarantined, not
deleted, and counted in `referential_integrity_failures`.

## 14. How do you handle late-arriving claims?
Defined here as `submission_date - service_date > 45 days` (the
generator's normal gap is 1-45 days; the injected late cohort is 91-240).
Late claims are valid, so they are FLAGGED (`is_late_arriving`,
`days_late`) and KEPT, never discarded, and counted in metrics. In
production they would trigger a backfill/reprocessing path for any
aggregates already computed.

## 15. Late-arriving data vs late-arriving dimensions vs out-of-order events?
Late-arriving DATA/facts: a fact (claim) arrives long after its event date -
what we flag here. Late-arriving DIMENSION: a dimension row (e.g. a
provider) referenced by facts that arrived before the dimension row did -
handled in Gold via how we join/version dimensions. Out-of-order events:
records processed in a different order than they occurred, independent of
business dates - addressed by ordering on event time, not arrival time.

## 16. How do you handle schema evolution across the claims batches?
`claims_batch_2` adds `adjustment_amount`. Readers use
`mergeSchema` so both batches load together; `ensure_columns`
guarantees the column exists so batch_1 rows get a null value. No business
meaning is invented for the missing column.

## 17. Why explicit Spark schemas instead of inference?
Bronze is entirely string-typed (ingestion writes `csv.DictReader`
output). Inference would guess types, require a full data scan, and hide bad
values as silent nulls. Explicit schemas (`schemas.py`) make the
contract visible and fail loudly on structural change.

## 18. How do Spark joins work, and what happens under the hood?
A join realigns rows by key. A shuffle (sort-merge/hash) join repartitions
both sides across the cluster by the join key - expensive. A broadcast join
ships the small side to every executor so the large side is never shuffled.

## 19. When would you use a broadcast join? Where here?
When one side is small enough to fit in memory. Here the dimension key sets
(members/providers/diagnoses) are small relative to claims, so they are
`F.broadcast`-ed into the claims referential-integrity joins to avoid
shuffling the larger fact data.

## 20. What causes a shuffle?
Wide operations: joins on non-broadcast keys, `groupBy`/aggregations,
`distinct`, repartition, and window functions that partition by a key.
This project keeps shuffles minimal (broadcast joins, small
`shuffle.partitions`) because the data is small.

## 21. repartition vs coalesce?
`repartition(n)` does a full shuffle and can increase or balance
partitions. `coalesce(n)` only merges existing partitions without a full
shuffle, so it is cheaper for REDUCING partition count (e.g. before a write)
but can create skew.

## 22. When should you cache?
Only when a DataFrame is reused across multiple actions and recomputation is
costly. This pipeline mostly runs linear write-once paths, so it does NOT
cache gratuitously - caching unused-once data just wastes memory. (The
repeated `count()` calls for metrics are an accepted tradeoff for
accuracy at this data size.)

## 23. How would this scale to millions of records/files?
The DataFrame code is already partition-aware. At scale you would size
`shuffle.partitions` to data volume, keep broadcasting only genuinely
small dimensions, partition Silver by date for pruning (already done for
claims), and replace per-run `count()` metrics with accumulators or
approximate counts to avoid extra passes.

## 24. How would this run on Databricks?
The same `pyspark.src` modules run as a Databricks job/notebook; you drop
the local `spark_session` config (the platform provides the session),
point input/output paths at DBFS/S3, and schedule it with Databricks
Workflows. No transformation code changes.

## 25. How would this run with AWS Glue?
Glue runs Spark too. You would package `pyspark/src` as a Glue job, read
Bronze from S3, write Silver back to S3, and register schemas in the Glue
Data Catalog (replacing local partition-directory listing with catalog
partitions). The transformation logic is unchanged; only IO and partition
discovery move to the catalog.

## 26. How would you monitor and recover this job?
Monitoring: the JSON data-quality metrics (counts, quarantine breakdown,
referential-integrity failures, late-arriving counts) are the natural signal
to alert on (e.g. quarantine rate spiking). Recovery: Silver writes in
`overwrite` mode and is a pure function of Bronze, so a failed or partial
run is fixed by simply re-running - it reproduces the same Silver state
rather than appending duplicates.

## 27. Do you guarantee exactly-once?
No, and the code does not claim to. Silver is reproducible/idempotent by
overwriting from Bronze (re-running yields the same result), which is
effectively at-least-once processing made safe by idempotent writes -
not a distributed exactly-once transaction guarantee.
