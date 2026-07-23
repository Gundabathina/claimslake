# spark_jobs/ - Silver transformation layer (Milestone 3)

This package is the single source of truth for the PySpark Bronze -> Silver
transformations. It reads raw Bronze Parquet (produced by the `ingestion/`
layer) and writes cleaned, validated, standardized data to `silver/`,
routing bad records to `silver/quarantine/` and writing data-quality
metrics to `data_quality/metrics/`.

```
SOURCE -> PYTHON INGESTION -> BRONZE -> PYSPARK SILVER -> (GOLD, later)
                                             |
                                             +--> QUARANTINE (rejected records)
```

## Package layout

```
spark_jobs/
|-- __init__.py
|-- README.md                 (this file)
|-- src/
    |-- __init__.py
    |-- spark_session.py      local SparkSession factory + config choices
    |-- schemas.py            explicit Bronze schemas + shared constants
    |-- readers.py            Bronze readers (full = latest partition; claims = mergeSchema)
    |-- cleaners.py           blank-to-null, type casting, batch canonicalization
    |-- deduplication.py      exact-row + deterministic business-key dedup
    |-- validators.py         business rules, referential integrity, quarantine, flags
    |-- transformations.py    per-dataset builders + real data-quality metrics
    |-- writers.py            Parquet + quarantine + JSON metrics
    |-- silver_pipeline.py    CLI entry point
```

Tests live in `tests/pyspark/`.

## Running it

Requires Python 3.11, `pyspark` (see `requirements.txt`), and a JVM
(Java 11 or 17) on the machine - Spark runs on the JVM. Bronze must be
populated first.

```
pip install -r requirements.txt
python -m ingestion.src.ingestion_engine --all      # SOURCE -> BRONZE
python -m spark_jobs.src.silver_pipeline --all          # BRONZE -> SILVER
python -m spark_jobs.src.silver_pipeline --source members
python -m spark_jobs.src.silver_pipeline --source claims
pytest tests/pyspark -v
```

CLI options: `--source {members,providers,diagnoses,claims}` or `--all`,
plus `--input-path`, `--output-path`, `--quarantine-path`,
`--metrics-path`.

## Key design decisions

### Explicit schemas, not inference
Bronze stores every column as a raw string (the ingestion layer reads CSVs
with `csv.DictReader` and writes strings to Parquet). So Silver defines
explicit schemas and does all type casting itself (`schemas.py`,
`cleaners.py`). Inference would guess types, cost a full scan, and hide
bad data. Explicit schemas make the Bronze -> Silver contract visible and
fail loudly on structural surprises.

### Full vs incremental reads
Full-load sources (members, providers, diagnoses) write a complete snapshot
into a new `ingestion_date=` partition each run, so Silver reads only the
LATEST partition. The incremental claims source appends genuinely new
batches, so Silver reads ALL partitions with `mergeSchema` enabled.

### Two kinds of duplicate
`drop_exact_duplicate_rows` collapses byte-identical business rows
(resent files). `deduplicate_by_key` picks one deterministic survivor per
business key (survivor = latest, tie broken by a content hash so it is
reproducible, not random).

### Providers preserve history for future SCD Type 2
Providers are deliberately NOT reduced to one row per provider. Rows sharing
a `provider_id` but differing in `network_status`/`effective_date`
are real historical versions and are kept as distinct rows (Silver grain =
one row per `(provider_id, effective_date)` version). Only true byte
duplicates are collapsed. This preserves the change signal the Gold layer
will turn into `valid_from`/`valid_to`/`is_current` (SCD Type 2).
The count of providers carrying history is reported as a metric.

### Claims grain, referential integrity, late-arriving, schema evolution
Claims grain is one surviving row per `claim_id`. Foreign keys
(member/provider/diagnosis) are checked with broadcast left joins against the
small Silver dimension key sets; unresolved keys are quarantined, not
dropped. Late-arriving claims (submission more than 45 days after service)
are FLAGGED and KEPT, never discarded. `claims_batch_2`'s extra
`adjustment_amount` column is carried into a canonical schema
(`mergeSchema` + `ensure_columns`); batch_1 rows get a null
`adjustment_amount` - no business value is invented.

### Quarantine, not deletion
Records failing validation go to `silver/quarantine/<dataset>/` carrying
`rejection_reason` and `validation_timestamp`. A record can list
multiple reasons. Non-fatal issues (missing zip, missing specialty,
duplicate NPI) are informational FLAG columns, never rejections.

### Partitioning
Silver claims are partitioned by `service_year_month` (claims analytics
filter by service-date ranges, so this enables partition pruning; year-month
avoids the tiny-file problem of per-day partitions at this volume).
Dimensions are NOT partitioned - they are small and read wholesale (and
broadcast), so partitioning would only create tiny files.

### Broadcast joins and shuffle partitions
Dimension key sets are broadcast into the claims foreign-key joins (small
side, avoids a shuffle). `spark.sql.shuffle.partitions` is lowered from
200 to 8 for local runs on this small dataset; on a real cluster it would be
sized to data volume. These are used only where they genuinely help, not for
show. Metrics use `count()` actions deliberately for accuracy; at scale
you would prefer accumulators/approximate counts.

## Honesty note

This code is committed via a browser-only environment that CANNOT run
Python/PySpark. It is code-complete and statically reviewed; the tests in
`tests/pyspark/` are written to execute real transformation logic but
have NOT been run here. Local execution (`pytest tests/pyspark -v` and a
full pipeline run) is still required to confirm results. All data is
synthetic. See `docs/interview_guide/03_pyspark_silver.md` for the
interview Q&A grounded in this implementation.
