# Changelog

All notable changes to ClaimsLake are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-30

First public release. ClaimsLake is a complete, portfolio-ready healthcare-claims
data engineering platform built on a medallion (Bronze/Silver/Gold) architecture
using synthetic data only.

### Completed milestones

- **Repository scaffolding** and synthetic data generators (members, providers, diagnoses, claims).
- **Bronze ingestion (Python):** config-driven full/incremental loads with retry handling, structured logging, and per-batch metadata tracking; raw Parquet output.
- **Silver transformations (PySpark):** typing, standardization, deterministic two-stage deduplication, business-rule validation, referential-integrity checks, late-arriving claim flagging, and a quarantine path that isolates invalid records with reasons instead of dropping them.
- **Gold star schema (dbt + dbt-duckdb):** `fact_claims`, `dim_member`, and `dim_provider` (SCD Type 2), built directly from the Silver Parquet via DuckDB, with dbt tests.
- **Analytical SQL layer:** 35 curated queries across members, providers, claims, finance, and data quality, plus a master runner and catalog.
- **Airflow orchestration:** a DAG wiring ingest, Silver, dbt build, and dbt test.
- **Expanded GitHub Actions CI:** four parallel jobs (unit tests for ingestion/SQL/scripts, PySpark Silver on JDK 17, Airflow DAG tests, and dbt parse), with pip caching.
- **Terraform AWS reference architecture:** S3 data-lake layers (encryption, versioning, public-access block, lifecycle rules), Glue Data Catalog with separate Silver and Gold crawlers, an Athena workgroup with encrypted results, and least-privilege IAM roles, organized into `s3`, `iam`, `glue`, and `athena` modules. Validated in CI (`fmt`, `init -backend=false`, `validate`).
- **End-to-end local runner:** `scripts/run_pipeline.py` executes Bronze -> Silver -> Gold.
- **Documentation:** recruiter-facing README with Mermaid diagrams, architecture/lineage/data-dictionary/analytics-catalog/interview-guide docs, and portfolio content.

### Verified results

- Bronze ingestion: 26 tests passing (verified locally).
- PySpark Silver: 17 tests passing (verified locally).
- dbt: PASS=14 (verified locally).
- SQL analytics: 35 curated queries.
- Airflow DAG tests: 7 passing (verified locally).
- CI (GitHub Actions): four application jobs green.
- Terraform CI: `fmt -check -recursive`, `init -backend=false`, and `validate` green.
- Docker Compose stack: `docker compose up --build` verified locally — Postgres healthy, Airflow metadata DB initialized, `airflow-init` completes, webserver and scheduler start, and the PySpark suite passes in the app container.

### Known limitations

- All data is synthetic; no real claims data is used anywhere.
- The Terraform AWS architecture is **reference-only and has never been planned or applied** — it creates no AWS resources or cost. `plan`/`apply` require AWS credentials.
- Streaming (Kafka) is **not implemented**; it remains optional future work.
- Test counts above were verified in earlier local runs; CI enforces the suites on every push.

### Future roadmap

- Publish a short screen capture of the full `docker compose up` stack running.
- Optional Kafka streaming demo for near-real-time claim events.
- Expand dbt tests and add exposures / generated docs.
- Optional (non-goal for this release): an actual AWS deployment of the Terraform reference architecture.

[1.0.0]: https://github.com/Gundabathina/claimslake/releases/tag/v1.0.0
