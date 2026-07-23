# docs/interview_guide/

Interview preparation material for discussing ClaimsLake in Data Engineer interviews.

## Milestone sections (added as each milestone is built)

- [Milestone 2 - Ingestion (Bronze)](02_ingestion_bronze.md) - 20 Q&A on the
  ingestion framework: architecture, idempotency, incremental vs CDC, schema
  drift, retries, metadata tracking, and how it would map to S3 / AWS Glue.
- [Milestone 3 - PySpark Silver](03_pyspark_silver.md) - 27 Q&A on the Silver
  layer: deduplication and business keys, provider history for SCD Type 2,
  quarantine, referential integrity, late-arriving claims, schema evolution,
  explicit schemas, broadcast joins, shuffles, partitioning, and how it would
  run on Databricks / AWS Glue.

## Planned (later milestones)

- 30-second, 2-minute, and 5-minute project pitches
- Why each technology was chosen, and what the alternatives were
- 20+ realistic interviewer questions with honest, defensible answers
- A dedicated "Things I must NOT claim" section listing the honest limitations of this project
