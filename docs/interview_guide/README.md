# docs/interview_guide/

Interview preparation material for discussing ClaimsLake in Data Engineer interviews. All data is synthetic.

## Project pitches and Q&A

Concise, ready-to-use pitches and interview answers live in
[`docs/portfolio_content.md`](../portfolio_content.md):

- 30-second and two-minute project explanations
- Ten realistic interview questions with technically accurate answers
- Resume bullets, LinkedIn description, and repository/topic content

## Deep-dive layer sections

- [Ingestion (Bronze)](02_ingestion_bronze.md) - 20 Q&A on the ingestion
  framework: architecture, idempotency, incremental vs CDC, schema drift,
  retries, metadata tracking, and how it would map to S3 / AWS Glue.
- [PySpark Silver](03_pyspark_silver.md) - 27 Q&A on the Silver layer:
  deduplication and business keys, provider history for SCD Type 2,
  quarantine, referential integrity, late-arriving claims, schema evolution,
  explicit schemas, broadcast joins, shuffles, partitioning, and how it would
  run on Databricks / AWS Glue.

## Honest limitations to keep in mind

When discussing the project, be accurate about what is and is not done:

- All data is synthetic; no real claims data is used.
- The Gold layer is built with dbt-duckdb (not Redshift); there is no cloud
  warehouse in the implementation.
- The full Docker Compose stack has not yet been verified end to end.
- The Terraform AWS architecture is reference-only and has never been applied.
- Streaming (Kafka) is not implemented and is optional future work.
